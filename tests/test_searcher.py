import unittest
from datetime import datetime, timezone
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

    @patch('jito_py.searcher.requests.get')
    def test_get_tip_floors(self, mock_get):
        # Real payload captured on 2026-10-24: the timestamp carries an explicit offset.
        mock_get.return_value.json.return_value = [{
            "time": "2026-10-24T12:27:34+00:00",
            "landed_tips_25th_percentile": 1.006e-06,
            "landed_tips_50th_percentile": 2.775e-06,
            "landed_tips_75th_percentile": 8.38475e-06,
            "landed_tips_95th_percentile": 0.00012206499999999988,
            "landed_tips_99th_percentile": 0.0020393,
            "ema_landed_tips_50th_percentile": 3.2894177320681444e-06,
        }]

        result = self.searcher.get_tip_floors()

        self.assertEqual(result.time, datetime(2026, 10, 24, 12, 27, 34, tzinfo=timezone.utc))
        self.assertEqual(result.landed_tips_lamports_25th_percentile, 1006)
        # float(2.775e-06) * 1e9 == 2774.9999999999995: truncation would give 2774.
        self.assertEqual(result.landed_tips_lamports_50th_percentile, 2775)
        self.assertEqual(result.landed_tips_lamports_95th_percentile, 122065)
        self.assertEqual(result.landed_tips_lamports_99th_percentile, 2039300)
        self.assertEqual(result.ema_landed_tips_lamports_50th_percentile, 3289)

        # A blocking HTTP call must always carry a timeout.
        self.assertEqual(mock_get.call_args.kwargs["timeout"], 10.0)

    @patch('jito_py.searcher.requests.get')
    def test_get_tip_floors_accepts_z_suffix(self, mock_get):
        # Older responses used a "Z" suffix; both forms must parse.
        mock_get.return_value.json.return_value = [{
            "time": "2025-03-12T15:38:27Z",
            "landed_tips_25th_percentile": 0.000001,
            "landed_tips_50th_percentile": 0.000002,
            "landed_tips_75th_percentile": 0.000003,
            "landed_tips_95th_percentile": 0.000004,
            "landed_tips_99th_percentile": 0.000005,
            "ema_landed_tips_50th_percentile": 0.000002,
        }]

        result = self.searcher.get_tip_floors(timeout=3)

        self.assertEqual(result.time, datetime(2025, 3, 12, 15, 38, 27, tzinfo=timezone.utc))
        self.assertEqual(result.landed_tips_lamports_99th_percentile, 5000)
        self.assertEqual(mock_get.call_args.kwargs["timeout"], 3)


if __name__ == "__main__":
    unittest.main()
