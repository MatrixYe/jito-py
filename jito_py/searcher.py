from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import requests

JITO_TIPS_ENDPOINT: str = "https://bundles.jito.wtf"


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
        """
        Parses a dictionary into a BundlesTipsFloorResponse object, converting the
        time string into a datetime object in UTC.
        """
        # Parse the ISO8601 time string (e.g., "2025-03-12T15:38:27Z") to a datetime object in UTC

        time_str = data.get("time")
        parsed_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        return BundlesTipsFloorResponse(
            time=parsed_time,
            landed_tips_lamports_25th_percentile=int(float(data.get("landed_tips_25th_percentile")) * (10 ** 9)),
            landed_tips_lamports_50th_percentile=int(float(data.get("landed_tips_50th_percentile")) * (10 ** 9)),
            landed_tips_lamports_75th_percentile=int(float(data.get("landed_tips_75th_percentile")) * (10 ** 9)),
            landed_tips_lamports_95th_percentile=int(float(data.get("landed_tips_95th_percentile")) * (10 ** 9)),
            landed_tips_lamports_99th_percentile=int(float(data.get("landed_tips_99th_percentile")) * (10 ** 9)),
            ema_landed_tips_lamports_50th_percentile=int(float(data.get("ema_landed_tips_50th_percentile")) * (10 ** 9))
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

    def get_tip_floors(self) -> BundlesTipsFloorResponse:
        """
        Retrieves the tips floor data for landed transactions. This data reflects the average SOL tip amounts
        based on various percentiles, which can be useful for understanding tip distributions for bundles and
        determining the optimal tip amount to land your transaction on Jito.

        The API response is expected to be a list of dictionaries with the following keys:
            - time
            - landed_tips_25th_percentile
            - landed_tips_50th_percentile
            - landed_tips_75th_percentile
            - landed_tips_95th_percentile
            - landed_tips_99th_percentile
            - ema_landed_tips_50th_percentile

        :return: A BundlesTipsFloorResponse object parsed from the API response.
        :raises Exception: If the API request fails or the response is invalid.
        """
        response = requests.get(f"{JITO_TIPS_ENDPOINT}/api/v1/bundles/tip_floor")
        response.raise_for_status()  # Raises an HTTPError for bad responses.
        data = response.json()
        if not data:
            raise Exception("No tip floor data available")

        # Extract the first dictionary from the list and parse it.
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
