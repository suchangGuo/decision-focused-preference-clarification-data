# Computational Environment

The released experiments were implemented in C# targeting .NET Framework 4.8
and executed on 64-bit Windows. Exact mixed-integer models were solved with IBM
ILOG CPLEX 22.2.0. The workstation processor was an AMD Ryzen 7 8840HX. CPLEX
used its default thread configuration unless a run log states otherwise.

Python scripts in `analysis_scripts` reproduce the reported data reductions
and publication figures from the released CSV files. They do not invoke the
optimization model.
