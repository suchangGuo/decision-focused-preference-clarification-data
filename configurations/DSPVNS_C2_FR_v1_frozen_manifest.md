# DSPVNS-C2-FR-v1.0 冻结清单

- 冻结日期：2026-11-04
- 用途：论文最终小规模精确性验证与后续数值实验
- 冻结原则：不再根据后续单个算例结果调整邻域、Shake、接收准则、C2 写入规则、前沿覆盖或路径重联参数。

## 1. 冻结结构

- VND 顺序：\(N_L\rightarrow N_T\rightarrow N_C\)
- Shake：多路径结构化破坏与重插，破坏比例 `0.20–0.60`，无改进时每次增加 `0.10`
- C1：规范化结构评价缓存
- C2：偏好无关的时间—信息非支配档案
- C3：完整子问题结果缓存
- 尺度/固定偏好问题：C2 引导的前沿覆盖重启
- 鲁棒问题：C2 后悔平衡重启与双侧锚点路径重联
- 路径重联中间方案：仅进入 C1，确认分支才按原支配规则提交 C2
- 额外 reconstruction 模块：禁用

## 2. 冻结参数

| Parameter | Value |
|---|---:|
| Maximum iterations per CEOP request | 200 |
| Maximum non-improvement iterations | 200 |
| Candidates per neighborhood | 5 |
| Time limit per CEOP request | 300 s |
| Initial / maximum Shake fraction | 0.20 / 0.60 |
| Shake increment | 0.10 |
| Maximum Shake attempts | 10 |
| C2 stagnation fraction | 0.20 |
| Maximum robust restarts | 2 |
| Maximum frontier-coverage restarts | 2 |
| Frontier candidate pool | 5 |
| Maximum path-relinking steps | 8 |
| Candidates per relinking step | 6 |

路径重联使用独立随机流。小规模最终实验中，首次鲁棒请求使用语义种子标签 `7`，后续参照一致化轮次依次递增。

## 3. 工具链

- .NET SDK：10.0.300
- Target framework：.NET Framework 4.8
- Platform：x64
- CPLEX assembly：22.2.0.0
- Release executable assembly：1.0.0.0

## 4. SHA-256

| File | SHA-256 |
|---|---|
| `VnsAlgorithm.cs` | `DFF9544E696B4022E1AC3E689B41B8DFCFC0001F3260924AF12A03545A7F15AB` |
| `C2GuidedSearchEnhancements.cs` | `6084E26A36F42C808528ED57FDA1F6B3E617661C34F4463A9E5C6D2D04D1D4E2` |
| `VnsModels.cs` | `83F463F65BC3449AE647B26E97621F03F82A77703433B047D99C2EE1C5D9D72E` |
| `VnsAccelerationCaches.cs` | `88EAE69814D24A612019B66234F8714BC192D2C1E8820C008E7454C9A87689A6` |
| `NeighborhoodAndShakeOperators.cs` | `D23208B1F59983CF62AC1745342F2FACFB3224AB0547F372A0D2024B5E24E360` |
| `ReconStructureTransformations.cs` | `0080A50695A365C23113C4640F0FA0F70F8BC05D399EF806851413529B837671` |
| `InitialSolutionConstruction.cs` | `BA45A90022C5300A82CCE8D3D455C009E56F5F713F1B3CAC5AE7E7CB2BAEE68F` |
| `SmallScaleComparisonRunner.cs` | `565A91CAAD2229D195436208919868C4AB1902C7144EABF87B2C848E1EC2D581` |
| `Program.cs` | `4F8C57E31EFA7DA18719EFBB5B081B7349B8071347B834A2644C1EAE79693D95` |
| `assistant.csproj` | `AC2798F4914F3C7452B2C435202CD835E0FF1705F465B0199B2DA799825C70E9` |
| `bin/Release/assistant.exe` | `F592849036389443021AECAA9BC7DB08E9B90D73DD4D6630EBCEED9D87460AA5` |

后续若上述文件哈希发生变化，应生成新的版本号和冻结清单，不得沿用 `DSPVNS-C2-FR-v1.0` 的数值实验结果口径。
