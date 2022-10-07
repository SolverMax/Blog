\ Model solved using the solver: CBC
\ Model for sheet Model 1
\ Model has 4  Excel constraints giving 7  constraint rows and 31  variables.
MINIMIZE
Obj: +0 B46 +0 B47 +0 B48 +0 B49 +0 B50 +0 B51 +0 B52 +0 B53 +0 B54 +0 B55 +0 B56 +0 B57 +0 B58 +0 B59 +0 B60 +0 B61 +0 B62 +0 B63 +0 B64 +0 B65 +0 B66 +0 B67 +0 B68 +0 B69 +0 B70 +0 B71 +0 B72 +0 B73 +0 B74 +0 B75 -1 K46
SUBJECT TO
\ J46 <= fUB
 -181.18 B46 -491.53 B47 -50.51 B48 -156.07 B49 -442.04 B50 -333.35 B51 -207.55 B52 -265.69 B53 -165.44 B54 -446.05 B55 -127.83 B56 -260.88 B57 -486.72 B58 -27.38 B59 -195.39 B60 -316.57 B61 -361.21 B62 -310.48 B63 -390.84 B64 -20.8499999999999 B65 -195.09 B66 -370.36 B67 -299.13 B68 -437.2 B69 -382.01 B70 -52.29 B71 -127.17 B72 -200.83 B73 -222 B74 -340.38 B75 +1 K46 <= -1048.67
\ J46 >= vLB
 -181.18 B46 -491.53 B47 -50.51 B48 -156.07 B49 -442.04 B50 -333.35 B51 -207.55 B52 -265.69 B53 -165.44 B54 -446.05 B55 -127.83 B56 -260.88 B57 -486.72 B58 -27.38 B59 -195.39 B60 -316.57 B61 -361.21 B62 -310.48 B63 -390.84 B64 -20.8499999999999 B65 -195.09 B66 -370.36 B67 -299.13 B68 -437.2 B69 -382.01 B70 -52.29 B71 -127.17 B72 -200.83 B73 -222 B74 -340.38 B75 -1 K46 >= -1048.67
\ I50:M50 <= fAllowed
\ (A row with all zero coeffs) <= +5
\ (A row with all zero coeffs) <= +4
\ (A row with all zero coeffs) <= +5
\ (A row with all zero coeffs) <= +5
\ (A row with all zero coeffs) <= +4

BOUNDS

\'Assume Non Negative' is FALSE, so default lower bounds of zero are removed from all non-binary variables.
 K46 FREE

BINARY
 B46 B47 B48 B49 B50 B51 B52 B53 B54 B55 B56 B57 B58 B59 B60 B61 B62 B63 B64 B65 B66 B67 B68 B69 B70 B71 B72 B73 B74 B75
END
