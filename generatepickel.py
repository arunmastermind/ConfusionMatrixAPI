import pandas as pd

df1 = pd.read_excel('test.xlsx')
df1.to_pickle('variousStates.pkl')
df2 = pd.read_pickle('variousStates.pkl')
print(df2)
# for _, row in df2.iterrows():
#     print(row)