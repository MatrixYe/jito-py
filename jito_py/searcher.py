from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import requests

JITO_TIPS_ENDPOINT: str = "https://bundles.jito.wtf"
JITO_TIP_FLOOR_TIMEOUT: float = 10.0

LAMPORTS_PER_SOL: int = 1_000_000_000


# noinspection SpellCheckingInspection
def _sol_to_lamports(value: Any) -> int:
    """Convert a SOL amount (str or number, as returned by the tip-floor API) to lamports.

    Uses round() rather than int() so floating point noise does not shave a lamport off
    (e.g. 0.00012206499999999988 SOL is 122065 lamports, not 122064).
    """
    return int(round(float(value) * LAMPORTS_PER_SOL))


def _parse_tip_floor_time(value: str) -> datetime:
    """Parse a tip-floor timestamp into an aware UTC datetime.

    The API returns ISO 8601 with an explicit offset ("2026-10-24T12:27:34+00:00");
    older responses used a "Z" suffix, so both forms are accepted.
    """
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass
class BundleStatus:
    bundle_id: str
    transactions: List[str]
    slot: int
    confirmation_status: str
    err: Dict[str, Any]


@dataclass
class BundleStatusesResponse:
    context_slot: int
    statuses: List[BundleStatus] = field(default_factory=list)


# noinspection SpellCheckingInspection
@dataclass
class BundlesTipsFloorResponse:
    time: datetime
    landed_tips_lamports_25th_percentile: int
    landed_tips_lamports_50th_percentile: int
    landed_tips_lamports_75th_percentile: int
    landed_tips_lamports_95th_percentile: int
    landed_tips_lamports_99th_percentile: int
    ema_landed_tips_lamports_50th_percentile: int

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BundlesTipsFloorResponse":
        """Parse one entry of the tip-floor API response.

        Percentile values arrive as SOL amounts and are converted to lamports here.
        """
        return BundlesTipsFloorResponse(
            time=_parse_tip_floor_time(data["time"]),
            landed_tips_lamports_25th_percentile=_sol_to_lamports(data["landed_tips_25th_percentile"]),
            landed_tips_lamports_50th_percentile=_sol_to_lamports(data["landed_tips_50th_percentile"]),
            landed_tips_lamports_75th_percentile=_sol_to_lamports(data["landed_tips_75th_percentile"]),
            landed_tips_lamports_95th_percentile=_sol_to_lamports(data["landed_tips_95th_percentile"]),
            landed_tips_lamports_99th_percentile=_sol_to_lamports(data["landed_tips_99th_percentile"]),
            ema_landed_tips_lamports_50th_percentile=_sol_to_lamports(data["ema_landed_tips_50th_percentile"]),
        )


class Searcher:
    def __init__(self, block_engine_url: str):
        self.block_engine_url = block_engine_url

    @staticmethod
    def _extract_result(response: Dict[str, Any], method: str) -> Any:
        if 'result' in response:
            return response['result']
        else:
            raise Exception(f"Error in {method} response: {response}")

    def _send_rpc_request(self, endpoint: str, method: str, params: Optional[List] = None) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        try:
            # url = f"{self.block_engine_url}/{endpoint}"
            url = f"{self.block_engine_url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = requests.post(url=url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {e}")

    def get_bundle_statuses(self, bundle_ids: List[str]) -> BundleStatusesResponse:
        """
        Returns the status of submitted bundle(s).

        :param bundle_ids: An array of bundle ids to confirm, as base-58 encoded strings (up to a maximum of 5).
        :return: A BundleStatusesResponse object containing the context slot and a list of BundleStatus objects.
        """
        response = self._send_rpc_request("/api/v1/bundles", "getBundleStatuses", [bundle_ids])
        result = self._extract_result(response, "getBundleStatuses")
        context_slot = result['context']['slot']
        statuses = [
            BundleStatus(
                bundle_id=status['bundle_id'],
                transactions=status['transactions'],
                slot=status['slot'],
                confirmation_status=status['confirmation_status'],
                err=status['err']
            )
            for status in result['value']
        ]
        return BundleStatusesResponse(context_slot=context_slot, statuses=statuses)

    def get_tip_accounts(self) -> List[str]:
        """
        Retrieves the tip accounts designated for tip payments for bundles.

        :return: Tip accounts as a list of strings.
        """
        response = self._send_rpc_request("/api/v1/bundles", "getTipAccounts")
        return self._extract_result(response, "getTipAccounts")

    @staticmethod
    def get_tip_floors(timeout: float = JITO_TIP_FLOOR_TIMEOUT) -> BundlesTipsFloorResponse:
        """
        Retrieves the tip floor data for recently landed bundles.

        The tip floor is the distribution of tips paid by bundles that landed, reported at the
        25th/50th/75th/95th/99th percentiles plus a 50th-percentile EMA. It is a useful reference
        for deciding how much tip to attach: too low and the bundle may lose the auction, too high
        and you overpay. Values are returned in lamports.

        Note this endpoint is a plain HTTP GET on bundles.jito.wtf, not a JSON-RPC call to a block
        engine, so it does not depend on ``self.block_engine_url``.

        The API response is expected to be a list of dictionaries with the following keys:
            - time
            - landed_tips_25th_percentile
            - landed_tips_50th_percentile
            - landed_tips_75th_percentile
            - landed_tips_95th_percentile
            - landed_tips_99th_percentile
            - ema_landed_tips_50th_percentile

        :param timeout: Seconds to wait for the HTTP request before failing.
        :return: A BundlesTipsFloorResponse object parsed from the API response.
        :raises Exception: If the API request fails or the response is invalid.
        """
        try:
            response = requests.get(
                f"{JITO_TIPS_ENDPOINT}/api/v1/bundles/tip_floor",
                timeout=timeout,
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses.
        except requests.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
        try:
            data = response.json()
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {e}")
        if not data:
            raise Exception("No tip floor data available")

        # The endpoint returns a single-element list; the first entry is the current tip floor.
        return BundlesTipsFloorResponse.from_dict(data[0])

    def send_bundle(self, transactions: List[str]) -> str:
        """
        Submits a bundled list of signed transactions (base-58 encoded strings) to the cluster for processing.

        :param transactions: Fully-signed transactions, as base-58 encoded strings (up to a maximum of 5).
                             Base-64 encoded transactions are not supported at this time.
        :return: A bundle ID, used to identify the bundle. This is the SHA-256 hash of the bundle's transaction signatures.
        """
        response = self._send_rpc_request("/api/v1/bundles", "sendBundle", [transactions])
        return self._extract_result(response, "sendBundle")

    def send_transaction(self, transaction: str) -> str:
        """
        This method serves as a proxy to the Solana sendTransaction RPC method. It forwards the received transaction as a
        regular Solana transaction via the Solana RPC method and submits it as a bundle. Jito sponsors the bundling and
        provides a minimum tip for the bundle. However, please note that this minimum tip might not be sufficient to get
        the bundle through the auction, especially during high-demand periods. If you set the query parameter bundleOnly=true,
        the transaction will only be sent out as a bundle and not as a regular transaction via RPC.

        :param transaction: First Transaction Signature embedded in the transaction, as base-58 encoded string.
        :return: The result will be the same as described in the Solana RPC documentation. If sending as a bundle was
                 successful, you can get the bundle_id for further querying from the custom header in the response x-bundle-id.
        """
        response = self._send_rpc_request("/api/v1/transactions", "sendTransaction", [transaction])
        return self._extract_result(response, "sendTransaction")
