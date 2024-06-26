import unittest
from unittest.mock import patch

from jito_py.searcher import Searcher, BundleStatusesResponse, BundleStatus


class TestSearcher(unittest.TestCase):
    def setUp(self):
        self.searcher = Searcher("https://mainnet.block-engine.jito.wtf")

    @patch('jito_py.searcher.requests.post')
    def test_get_tip_accounts(self, mock_post):
        mock_post.return_value.json.return_value = {
            "jsonrpc": "2.0",
            "result": [
                "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
                "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
                "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
                "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
                "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
                "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
                "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
                "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
            ],
            "id": 1
        }
        expected_response = [
            "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
            "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
            "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
            "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
            "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
            "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
            "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
            "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
        ]

        result = self.searcher.get_tip_accounts()
        print(result)

        self.assertEqual(result, expected_response)

    @patch('jito_py.searcher.requests.post')
    def test_get_bundle_statuses(self, mock_post):
        mock_post.return_value.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "context": {
                    "slot": 242806119
                },
                "value": [
                    {
                        "bundle_id": "892b79ed49138bfb3aa5441f0df6e06ef34f9ee8f3976c15b323605bae0cf51d",
                        "transactions": [
                            "3bC2M9fiACSjkTXZDgeNAuQ4ScTsdKGwR42ytFdhUvikqTmBheUxfsR1fDVsM5ADCMMspuwGkdm1uKbU246x5aE3",
                            "8t9hKYEYNbLvNqiSzP96S13XF1C2f1ro271Kdf7bkZ6EpjPLuDff1ywRy4gfaGSTubsM2FeYGDoT64ZwPm1cQUt"
                        ],
                        "slot": 242804011,
                        "confirmation_status": "finalized",
                        "err": {
                            "Ok": None
                        }
                    }
                ]
            },
            "id": 1
        }
        expected_response = BundleStatusesResponse(
            context_slot=242806119,
            statuses=[
                BundleStatus(
                    bundle_id="892b79ed49138bfb3aa5441f0df6e06ef34f9ee8f3976c15b323605bae0cf51d",
                    transactions=[
                        "3bC2M9fiACSjkTXZDgeNAuQ4ScTsdKGwR42ytFdhUvikqTmBheUxfsR1fDVsM5ADCMMspuwGkdm1uKbU246x5aE3",
                        "8t9hKYEYNbLvNqiSzP96S13XF1C2f1ro271Kdf7bkZ6EpjPLuDff1ywRy4gfaGSTubsM2FeYGDoT64ZwPm1cQUt"
                    ],
                    slot=242804011,
                    confirmation_status="finalized",
                    err={"Ok": None}
                )
            ]
        )
        result = self.searcher.get_bundle_statuses(["892b79ed49138bfb3aa5441f0df6e06ef34f9ee8f3976c15b323605bae0cf51d"])
        print(result)
        self.assertEqual(result, expected_response)


if __name__ == "__main__":
    unittest.main()
