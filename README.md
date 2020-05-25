# Phi accrual failure detector with cold restarts

Well-known failure detectors (FD), such as the Phi-accrual FD, usually use the *crash-stop* model and assume there is no chance for **recovery**. However, under special cases where devices are extremely unstable and **frequently stop and later recover**, this assumption does not hold.

Actually, this is what we face when building the prototype of [FPGAOL](https://fpgaol.ustc.edu.cn/). Problems such as power failures, network failures and sometimes software errors may keep one node down for a period of time, but the devices could get back online very soon without human interference. However, for the QoS requirements of FPGAOL, we need to know the exact running state of a node and **"predict" whether they could keep stable in the next few minutes**.

## The solution: Add cold restarts!



| Phi  | CS-Phi |
| :--: | :----: |
| 124  |   80   |

|        | Accuracy | Recall |
| :----: | :------: | :----: |
|  Phi   |  0.999   | 0.998  |
| CS-Phi |  0.975   | 0.999  |