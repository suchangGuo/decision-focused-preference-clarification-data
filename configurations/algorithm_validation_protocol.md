# CPLEX 与 DSPVNS-C2-FR-v1.0 小规模精确性验证规范

## 1. 实验任务

本实验用于检验冻结算法 `DSPVNS-C2-FR-v1.0` 在小规模算例上的求解精度、稳定性和计算时间。CPLEX 提供经最优性证明的参照值，精确尺度和精确端点参照值仅用于启发式结果的事后统一评价。

## 2. 算例组

| Scale | Random | Clustered | Mixed |
|---|---|---|---|
| \(N=6,U=2\) | `6-2-R` | `6-2-C` | `6-2-RC` |
| \(N=9,U=3\) | `9-3-R` | `9-3-C` | `9-3-RC` |

统一设置：

- 算例种子：`20261011`；
- 侦察等级数：\(L=3\)；
- 偏好歧义集：\([0.30,0.70]\)；
- 空间结构：Solomon `R101`、`C101` 和 `RC101`。

## 3. 求解协议

### 3.1 CPLEX

每个算例运行一次完整的精确求解链。相对和绝对 MIP gap 均设为 0，不设求解时限。只有可行性校验通过且 MIP gap 为 0 的结果才进入最终汇总表。

### 3.2 DSPVNS-C2-FR-v1.0

每个算例独立运行 5 次，基础算法种子为：

`2026110301, 2026110302, 2026110303, 2026110304, 2026110305`

每次完整运行使用独立的 C1、C2 和 C3。冻结参数与 `DSPVNS-C2-FR-v1.0` 冻结清单一致，其中：

- 每个 CEOP 请求最多 200 次外层迭代；
- VND 顺序为 \(N_L\rightarrow N_T\rightarrow N_C\)；
- Shake 破坏比例为 `0.20–0.60`；
- C2 前沿覆盖重启、后悔平衡重启和双侧路径重联均启用；
- 额外 reconstruction 模块禁用；
- 路径重联使用独立随机流；
- 首次鲁棒请求使用语义种子标签 `7`。

## 4. 评价指标

设 CPLEX 最优值为 \(z^*\)，第 \(r\) 次 DSPVNS 的事后可比目标值为 \(z_r\)。汇总指标为：

\[
\bar z=\frac{1}{5}\sum_{r=1}^{5}z_r,
\qquad
z^{\mathrm{best}}=\min_{r=1,\ldots,5}z_r,
\]

\[
\operatorname{Gap}(\%)=
\frac{\bar z-z^*}{|z^*|}\times100\%,
\qquad
\operatorname{CV}(\%)=
\frac{s(z_1,\ldots,z_5)}{\bar z}\times100\%.
\]

其中 \(s(\cdot)\) 为样本标准差。

## 5. 最终论文表格口径

| Instance | CPLEX Obj. | CPLEX Time (s) | DSPVNS Avg. Obj. | DSPVNS Best Obj. | DSPVNS Avg. Time (s) | Gap (%) | CV (%) |
|---|---:|---:|---:|---:|---:|---:|---:|

目标值在论文表中统一显示 5 位小数，原始工作表保留 10 位小数。时间指标均为从尺度标定开始到最终鲁棒方案返回为止的端到端墙钟时间。

## 6. 输出

- 原始日志：`small_scale_experiment_raw_DSPVNS_C2_FR_v1.log`
- 最终工作簿：`CPLEX_vs_DSPVNS_C2_FR_v1_final.xlsx`
- 工作表：`Summary`、`CPLEX_Raw`、`DSPVNS_Raw` 和 `Settings`

最终表格用于小规模精确性与稳定性验证。它不用于宣称算法的通用优越性，也不单独识别 C2 前沿覆盖和路径重联的独立贡献。
