# 测试scikit-learn是否能正常导入
import time
print("开始导入scikit-learn...")
start = time.time()
from sklearn.cluster import KMeans
end = time.time()
print(f" scikit-learn导入成功，耗时：{end-start:.2f}秒")