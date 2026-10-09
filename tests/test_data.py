"""공개 페이지의 Next.js 누락 값 때문에 표 생성이 중단된 오류의 회귀 검사."""
import math
import unittest
from unittest.mock import patch

from ai_analysis import data as d


class SourceNumbersTest(unittest.TestCase):
    def test_empty_conversion_does_not_replace_cache_or_fetch_livebench(self):
        raw = [{"slug": "invalid", "intelligenceIndex": 45, "intelligenceIndexCostPerTask": "$undefined"}]
        with (patch.object(d, "fetch", return_value="source"),
              patch.object(d, "parse", return_value=raw),
              patch.object(d, "fetch_livebench") as livebench,
              patch.object(d.Path, "write_text") as write):
            with self.assertRaisesRegex(ValueError, "유효한 모델이 없습니다"):
                d.load(refresh=True)
        livebench.assert_not_called()
        write.assert_not_called()

    def test_nextjs_missing_values_do_not_break_model_conversion(self):
        html = (
            r'{\"slug\":\"missing-cost\",\"intelligenceIndex\":45,\"intelligenceIndexCostPerTask\":\"$undefined\"}'
            r'{\"slug\":\"valid\",\"intelligenceIndex\":45,\"intelligenceIndexCostPerTask\":0.2,\"medianEndToEndResponseTimeSeconds\":\"$undefined\",\"medianOutputTokensPerSecond\":\"$undefined\",\"medianTimeToFirstTokenSeconds\":\"$undefined\",\"terminalBench40\":0}'
        )
        models = d.to_models(d.parse(html))
        self.assertEqual([model.name for model in models], ["valid"])
        model = models[0]
        self.assertEqual(model.cost, 0.2)
        self.assertIsNone(model.time)
        self.assertIsNone(model.tps)
        self.assertIsNone(model.ttft)
        self.assertEqual(d.cells(model)["time"], "-")
        self.assertEqual(d.cells(model)["tb"], "0.0%")

    def test_invalid_required_metrics_are_excluded_and_numeric_strings_work(self):
        base = {"slug": "model", "intelligenceIndex": 45, "intelligenceIndexCostPerTask": 0.2}
        for key in ["intelligenceIndex", "intelligenceIndexCostPerTask"]:
            for value in [None, "$undefined", "NaN", "Infinity", math.nan, math.inf, True, 10**1000]:
                with self.subTest(key=key, value=value):
                    self.assertEqual(d.to_models([dict(base, **{key: value})]), [])
        for cost in [0, -1]:
            self.assertEqual(d.to_models([dict(base, intelligenceIndexCostPerTask=cost)]), [])
        model = d.to_models([dict(base, intelligenceIndex="45.2", intelligenceIndexCostPerTask="0.3", medianEndToEndResponseTimeSeconds="15.9")])[0]
        self.assertEqual(d.cells(model)["time"], "15.9s")
        self.assertEqual(model.score, 45.2)


if __name__ == "__main__":
    unittest.main()
