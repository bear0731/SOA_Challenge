0) 你目前最重要的「總結訊號」

你印出的總量指標是：

Overall A/E（Count）= 1.0732

Overall A/E（Amount）= 0.9105

ilec_comprehensive_eda

ilec_comprehensive_eda

這組合本身就是個紅旗：事件比預期多，但金額比預期少。
它通常不是一句「模型不準」能帶過，而是暗示 mix / selection / 金額結構 在不同子群間不一致（我下面會教你怎麼拆）。

1) 我先「抓錯」：最可能造成誤解的點（按嚴重度排序）
A. 你把 Duration pattern 當成「純 duration 效果」的風險很高

你在 notebook 裡把 duration 當成主要切片（還做了「select period analysis」）

ilec_comprehensive_eda

。
但在 ILEC 這種 policy-year-cell aggregated + observation year 被固定/混合的資料裡，duration 幾乎必然混了 cohort（Issue Year）與 period（Observation Year）。這會導致：

你看到的「前幾年比較低」不一定是核保 select effect

可能是 新 cohort 的 base mortality / underwriting / mix 不同

也可能是 survivorship（留下來的） + lapse/termination selection

Reviewer 會問：你有沒有在 固定 Issue cohort 的條件下再看一次 duration？如果沒有，你現在的 duration 結論必須降調。

B. 你用「平均 A/E」很可能是錯的統計量（或至少需要雙版本）

你輸出「WLT Average A/E」「PLT Average A/E」

ilec_comprehensive_eda

。
如果這個 average 是「對每個 cell 的 A/E 取 mean」，它會被 小暴險 cell 嚴重影響（甚至比大暴險更有話語權）。這在 A/E 分析是常見硬傷。

正確應同時報兩種：

Ratio of sums：sum(A) / sum(E)（最標準）

Mean of ratios：mean(A/E)（只用來看分佈，不用來當 KPI）

你現在 summary 看起來偏像 #2（需回頭確認 code）；即使你後面有用加總算 overall A/E（你確實有）

ilec_comprehensive_eda

，WLT/PLT 的 average A/E 仍可能被誤讀。

C. WLT vs PLT 的比較高度可能是「mix confounding」，不是 type effect

你顯示：

WLT Average A/E ≈ 0.995

PLT Average A/E ≈ 1.446
且 PLT death rate 也更高

ilec_comprehensive_eda

這看起來像「PLT 比 WLT 危險很多」，但 reviewer 會第一時間問：

兩者的 attained age 分佈 一樣嗎？

兩者的 duration 分佈 一樣嗎？

兩者的 smoker / preferred class / sex mix 一樣嗎？

只要分佈不一樣（幾乎必然不一樣），你現在的結論就不能寫成「PLT 造成較高 mortality」，最多只能寫成：

“In this dataset, PLT records exhibit higher observed mortality and A/E than WLT, without yet controlling for mix differences.”

D. 你把 duration 限在 1–50：合理，但要說清楚「你在做 truncation」

你在 AE vs Duration 圖上只顯示 duration 1–50

ilec_comprehensive_eda

。
這是合理的工程選擇，但在報告裡要明講：你把 tail cut 掉了，否則 reviewer 會追問「長尾是否反轉？」或「高 duration 是否 sample selection 極強？」

2) 哪些結論站得住？哪些要收斂？（按你最後 Key Findings 逐條審）

你最後的 Key Findings 包含：

Age effect 指數上升

男性高於女性

吸菸者高於非吸菸

Select period：前期較低（selection effect）

Preferred class 較低

ilec_comprehensive_eda

✅ 站得住（可以寫得比較肯定）

Age effect、Sex effect、Smoking effect、Preferred class effect
這些在死亡經驗資料中是強訊號；即便有 mix/selection，它們的方向通常穩健

ilec_comprehensive_eda

。
不過更專業的寫法會加一句：“observed in aggregated experience; not fully mix-adjusted”。

⚠️ 要收斂（不能寫太滿）

「Select period → selection effect」 這條要降調
因為你目前的 duration 分析沒有明確展示「固定 issue cohort / 控制 observation year」的識別設計；在這種資料形態下，duration pattern 是最容易被 cohort/period artefact 偽造的。

建議你把文字改成：

“Early durations show lower observed mortality consistent with selection, but this pattern may also reflect cohort/period composition and survivorship; further cohort-conditioned analysis is required.”

3) A/E 深度診斷：你現在最該做的 3 個拆解

你目前已經算出 overall A/E（count 與 amount）

ilec_comprehensive_eda

。下一步請不要急著建模，先把 A/E 拆成「可被質疑的假設」：

(1) Count vs Amount 的矛盾要被解釋

A/E count > 1 但 amount < 1

ilec_comprehensive_eda


最常見解釋是：死亡事件集中在 低保額/低金額暴險 的 cells。

你下一步應該做：

以 Face Amount band（或 Amount Exposed band） 分層算 sum(A)/sum(E)（count & amount 都算）

看矛盾是不是只出現在某些 band

(2) 把 A/E 寫成「mix 的乘積」，避免口水仗

你可以用這句對主管/ reviewer 很有效：

Amount A/E ≈ Count A/E × (Actual avg claim / Expected avg claim)

你現在這組數字意味著：

Actual avg claim 明顯低於 Expected avg claim（因為 0.9105 / 1.0732 < 1）

這比「模型錯」更像「結構錯（mix/selection）」。

(3) PLT 的 A/E 高：很可能是「post-level-term 的反向 selection」訊號

你畫的是 AE vs Duration（WLT vs PLT）

ilec_comprehensive_eda

。
PLT 本身在保險行為上常對應：保費跳升、續保決策、lapse/anti-selection。
所以如果 PLT A/E 偏高，合理假說不是「PLT 造成死亡」，而是：

留在 PLT 的人 ≠ 隨機子樣本

可能是健康差的人更留、健康好的人更走（或反過來，取決於產品/市場）

你要做的是：在同 attained age、同 duration band、同 preferred/smoker/sex 下比 WLT vs PLT 的 A/E（見下一步）。

4) Duration / Select effect：你要怎麼把它做成「可 defend」的識別？

你目前有「Duration Mortality Curve（Select Period Analysis）」的程式碼

ilec_comprehensive_eda

。
要把它變成 reviewer 不會打臉的版本，你需要至少做到其中一個：

✅ 最推薦：固定 Issue cohort（Issue Year 區間），看 duration 曲線

例如：

Issue Year ∈ [2005–2009]

Issue Year ∈ [2010–2014]

Issue Year ∈ [2015–2019]

各自畫 duration 1–15 的 A/E（或死亡率）。
如果每個 cohort 都呈現「前低後收斂」，你才能比較敢說 selection effect。

✅ 其次：固定 Observation Year，看 duration（但要明講混 cohort）

如果你固定 2019 年，那 duration = 1,2,3… 對應不同 issue year。
你可以做，但必須把它當成 APC 混合結果 描述，而非 causal duration。