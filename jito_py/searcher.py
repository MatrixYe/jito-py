from dataclasses import dataclass, field
from typing import List, Optional

import requests


@dataclass
class BundleStatus:
    bundle_id: str
    transactions: List[str]
    slot: int
    confirmation_status: str
    err: dict


@dataclass
class BundleStatusesResponse:
    context_slot: int
    statuses: List[BundleStatus] = field(default_factory=list)


class Searcher:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url

    def _send_rpc_request(self, method: str, params: Optional[List] = None) -> dict:
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        response = requests.post(self.rpc_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_bundle_statuses(self, bundle_ids: List[str]) -> BundleStatusesResponse:
        """
        Returns the status of submitted bundle(s).
        :param bundle_ids:  An array of bundle ids to confirm, as base-58 encoded strings (up to a maximum of 5).
        :return: A BundleStatusesResponse object containing the context slot and a list of BundleStatus objects.
        """
        response = self._send_rpc_request("getBundleStatuses", [bundle_ids])
        if 'result' in response:
            context_slot = response['result']['context']['slot']
            statuses = [
                BundleStatus(
                    bundle_id=status['bundle_id'],
                    transactions=status['transactions'],
                    slot=status['slot'],
                    confirmation_status=status['confirmation_status'],
                    err=status['err']
                )
                for status in response['result']['value']
            ]
            return BundleStatusesResponse(context_slot=context_slot, statuses=statuses)
        else:
            raise Exception(f"Error in getBundleStatuses response: {response}")

    def get_tip_accounts(self) -> List[str]:
        """
         Retrieves the tip accounts designated for tip payments for bundles.

         :param: null
         :return: Tip accounts as a list of strings
         """

        response = self._send_rpc_request("getTipAccounts")
        if 'result' in response:
            return response['result']
        else:
            raise Exception(f"Error in getTipAccounts response: {response}")

    def send_bundle(self, transactions: List[str]) -> str:
        """
        Submits a bundled list of signed transactions (base-58 encoded strings) to the cluster for processing

        :param transactions: Fully-signed transactions, as base-58 encoded strings (up to a maximum of 5). Base-64 encoded transactions are not supported at this time
        :return: A bundle ID, used to identify the bundle. This is the SHA-256 hash of the bundle's transaction signatures.
        """
        response = self._send_rpc_request("sendBundle", [transactions])
        if 'result' in response:
            return response['result']
        else:
            raise Exception(f"Error in sendBundle response: {response}")

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
        response = self._send_rpc_request("sendTransaction", [transaction])
        if 'result' in response:
            return response['result']
        else:
            raise Exception(f"Error in sendTransaction response: {response}")
