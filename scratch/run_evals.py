import sys
import os
import json
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.quant_agent import perform_lynch_analysis
from agent.kpi_agent import perform_kpi_analysis

def load_dataset(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "eval_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"[Error] Dataset file not found at: {dataset_path}")
        sys.exit(1)
        
    dataset = load_dataset(dataset_path)
    
    total_quant_metrics = 0
    correct_quant_metrics = 0
    total_kpi_metrics = 0
    correct_kpi_metrics = 0
    
    quant_score_diffs = []
    kpi_score_diffs = []
    composite_score_diffs = []
    
    correct_category = 0
    correct_verdict = 0
    
    test_cases_status = []
    
    print("=" * 100)
    print("RUNNING PETER LYNCH STOCK RESEARCH AGENT EVALUATIONS")
    print("=" * 100)
    
    for symbol, ground_truth in dataset.items():
        print(f"\nEvaluating {symbol}...")
        
        try:
            # 1. Run Quant Analysis
            quant_results = perform_lynch_analysis(symbol)
            
            # 2. Run KPI Analysis
            kpi_results = perform_kpi_analysis(symbol)
            
            # Calculate composite
            calc_quant_score = quant_results.get("quant_score", 0)
            calc_kpi_score = kpi_results.get("kpi_score", 0)
            calc_composite_score = calc_quant_score + calc_kpi_score
            
            # Verdict calculation
            if calc_composite_score >= 80:
                calc_verdict = "STRONG BUY"
            elif calc_composite_score >= 65:
                calc_verdict = "BUY"
            elif calc_composite_score >= 50:
                calc_verdict = "WATCH"
            elif calc_composite_score >= 35:
                calc_verdict = "NEUTRAL"
            else:
                calc_verdict = "AVOID"
                
            calc_category = quant_results.get("lynch_category", "Unknown")
            
            # Compare Quant Scores
            gt_quant = ground_truth["quant"]
            gt_quant_scores = gt_quant["scores"]
            calc_quant_scores = quant_results["scores"]
            
            quant_match = True
            for metric, expected_score in gt_quant_scores.items():
                actual_score = calc_quant_scores.get(metric, 0)
                total_quant_metrics += 1
                if actual_score == expected_score:
                    correct_quant_metrics += 1
                else:
                    quant_match = False
                    print(f"  [Quant Mismatch] Metric: {metric} | Expected: {expected_score} | Actual: {actual_score}")
                    
            if calc_quant_score != gt_quant["quant_score"]:
                quant_match = False
                print(f"  [Quant Mismatch] Total Quant Score | Expected: {gt_quant['quant_score']} | Actual: {calc_quant_score}")
                
            if calc_category != gt_quant["lynch_category"]:
                quant_match = False
                print(f"  [Category Mismatch] Expected: {gt_quant['lynch_category']} | Actual: {calc_category}")
            else:
                correct_category += 1
                
            quant_score_diffs.append(abs(calc_quant_score - gt_quant["quant_score"]))
            
            # Compare KPI Scores
            gt_kpi = ground_truth["kpi"]
            gt_kpi_scores = gt_kpi["scores"]
            calc_kpi_scores = kpi_results["scores"]
            
            kpi_match = True
            for metric, expected_score in gt_kpi_scores.items():
                actual_score = calc_kpi_scores.get(metric, 0)
                total_kpi_metrics += 1
                if actual_score == expected_score:
                    correct_kpi_metrics += 1
                else:
                    kpi_match = False
                    print(f"  [KPI Mismatch] Metric: {metric} | Expected: {expected_score} | Actual: {actual_score}")
                    
            if calc_kpi_score != gt_kpi["kpi_score"]:
                kpi_match = False
                print(f"  [KPI Mismatch] Total KPI Score | Expected: {gt_kpi['kpi_score']} | Actual: {calc_kpi_score}")
                
            kpi_score_diffs.append(abs(calc_kpi_score - gt_kpi["kpi_score"]))
            
            # Compare Composite
            gt_composite = ground_truth["composite"]
            composite_match = True
            if calc_composite_score != gt_composite["composite_score"]:
                composite_match = False
                print(f"  [Composite Mismatch] Expected: {gt_composite['composite_score']} | Actual: {calc_composite_score}")
                
            if calc_verdict != gt_composite["verdict"]:
                composite_match = False
                print(f"  [Verdict Mismatch] Expected: {gt_composite['verdict']} | Actual: {calc_verdict}")
            else:
                correct_verdict += 1
                
            composite_score_diffs.append(abs(calc_composite_score - gt_composite["composite_score"]))
            
            # Overall Status
            case_passed = quant_match and kpi_match and composite_match
            test_cases_status.append({
                "symbol": symbol,
                "passed": case_passed,
                "quant": f"{calc_quant_score}/{gt_quant['quant_score']}",
                "kpi": f"{calc_kpi_score}/{gt_kpi['kpi_score']}",
                "composite": f"{calc_composite_score}/{gt_composite['composite_score']}",
                "category": f"{calc_category} (Exp: {gt_quant['lynch_category']})",
                "verdict": f"{calc_verdict} (Exp: {gt_composite['verdict']})"
            })
            
            if case_passed:
                print(f"  PASS! Composite Score: {calc_composite_score}/100 | Verdict: {calc_verdict}")
            else:
                print(f"  FAIL! Check details above.")
                
        except Exception as e:
            print(f"  [Exception] Failed to evaluate {symbol}: {e}")
            traceback.print_exc()
            test_cases_status.append({
                "symbol": symbol,
                "passed": False,
                "error": str(e)
            })
            
    # Evaluation Calculations
    quant_metric_accuracy = (correct_quant_metrics / total_quant_metrics) * 100 if total_quant_metrics > 0 else 0
    kpi_metric_accuracy = (correct_kpi_metrics / total_kpi_metrics) * 100 if total_kpi_metrics > 0 else 0
    
    quant_mae = sum(quant_score_diffs) / len(quant_score_diffs) if quant_score_diffs else 999
    kpi_mae = sum(kpi_score_diffs) / len(kpi_score_diffs) if kpi_score_diffs else 999
    composite_mae = sum(composite_score_diffs) / len(composite_score_diffs) if composite_score_diffs else 999
    
    verdict_accuracy = (correct_verdict / len(dataset)) * 100 if dataset else 0
    category_accuracy = (correct_category / len(dataset)) * 100 if dataset else 0
    
    overall_passed = all(tc["passed"] for tc in test_cases_status)
    
    # Render final report
    print("\n" + "=" * 100)
    print("EVALUATION RESULTS SUMMARY REPORT")
    print("=" * 100)
    
    print("\nIndividual Test Case Breakdown:")
    print(f"{'Ticker':<10} | {'Status':<6} | {'Quant Score':<12} | {'KPI Score':<12} | {'Composite':<12} | {'Verdict':<25}")
    print("-" * 100)
    for tc in test_cases_status:
        status_str = "PASS" if tc.get("passed") else "FAIL"
        if "error" in tc:
            print(f"{tc['symbol']:<10} | {'ERROR':<6} | {tc['error'][:60]}")
        else:
            print(f"{tc['symbol']:<10} | {status_str:<6} | {tc['quant']:<12} | {tc['kpi']:<12} | {tc['composite']:<12} | {tc['verdict']:<25}")
            
    print("\nAggregate Scoring Accuracy Metrics:")
    print(f"  * Quant Metric Score Match Rate:  {quant_metric_accuracy:6.2f}% ({correct_quant_metrics}/{total_quant_metrics})")
    print(f"  * KPI Metric Score Match Rate:    {kpi_metric_accuracy:6.2f}% ({correct_kpi_metrics}/{total_kpi_metrics})")
    print(f"  * Category Classification Rate:   {category_accuracy:6.2f}% ({correct_category}/{len(dataset)})")
    print(f"  * Verdict Classification Rate:    {verdict_accuracy:6.2f}% ({correct_verdict}/{len(dataset)})")
    print(f"  * Quant Total Score MAE:          {quant_mae:6.2f} pts")
    print(f"  * KPI Total Score MAE:            {kpi_mae:6.2f} pts")
    print(f"  * Composite Score MAE:            {composite_mae:6.2f} pts")
    
    print("\n" + "=" * 100)
    if overall_passed:
        print("OVERALL EVALUATION PASSED! All scoring calculations and categories match the ground truth.")
        print("=" * 100)
        sys.exit(0)
    else:
        print("OVERALL EVALUATION FAILED! One or more mismatches found. Verify calculations or ground truth.")
        print("=" * 100)
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation()
