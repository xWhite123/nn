001
002
003
004
005
006
007
008
009
010
011
012
013
014
015
016
017
018
019
020
021
022
023
024
025
026
027
028
029
030
031
032
033
034
035
036
037
038
039
040
041
042
043
044
045
046
047
048
049
050
051
052
053
054
055
056
057
058
059
060
061
062
063
064
065
066
067
068
069
070
071
072
073
074
075
076
077
078
079
080
081
082
083
084
085
086
087
088
089
090
091
092
093
094
095
096
097
098
099
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
151
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
177
178
179
180
181
182
183
184
185
186
187
188
189
190
191
192
193
194
195
196
197
198
199
200
201
202
203
204
205
206
207
208
209
210
211
212
213
214
215
216
217
218
219
220
221
222
223
224
225
226
227
228
229
230
231
232
233
234
235
236
237
238
239
240
241
242
243
244
245
246
247
248
249
250
251
252
253
254
255
256
257
258
259
260
261
262
263
264
265
266
267
268
269
270
271
272
273
274
275
276
277
278
279
280
281
282
283
284
285
286
287
288
289
290
291
292
293
294
295
296
297
298
299
300
301
302
303
304
305
306
307
308
# 导入NumPy库，用于科学计算和数值操作
import numpy as np
# 导入matplotlib.pyplot模块，用于数据可视化和绘图
import matplotlib.pyplot as plt 
 
# 生成混合高斯分布数据
def generate_data(n_samples=1000):
    """生成混合高斯分布数据集
     
    参数:
        n_samples: 总样本数量 (默认=1000)
     
    返回:
        X: 特征矩阵 (n_samples, 2)
        y_true: 真实标签 (n_samples,)
    """
    np.random.seed(42)  # 固定随机种子以确保结果可复现
    # 定义三个高斯分布的中心点
    mu_true = np.array([ 
        [0, 0],  # 第一个高斯分布的均值
        [5, 5],  # 第二个高斯分布的均值
        [-5, 5]  # 第三个高斯分布的均值
    ])
     
    # 定义三个高斯分布的协方差矩阵
    sigma_true = np.array([
        [[1, 0], [0, 1]],  # 第一个分布：圆形分布(各向同性)
        [[2, 0.5], [0.5, 1]],  # 第二个分布：倾斜的椭圆
        [[1, -0.5], [-0.5, 2]]  # 第三个分布：反向倾斜的椭圆
    ])
     
    # 定义每个高斯分布的混合权重(必须和为1)
    weights_true = np.array([0.3, 0.4, 0.3])
     
    # 获取混合成分的数量(这里是3)
    n_components = len(weights_true)
     
    # 生成一个合成数据集，该数据集由多个多元正态分布的样本组成
    samples_per_component = (weights_true * n_samples).astype(int)
     
    # 确保样本总数正确（由于浮点转换可能有误差）
    total_samples = np.sum(samples_per_component)
    if total_samples < n_samples:
        # 将缺少的样本添加到权重最大的成分中
        samples_per_component[np.argmax(weights_true)] += n_samples - total_samples
     
    # 用于存储每个高斯分布生成的数据点
    X_list = []  
     
    # 用于存储每个数据点对应的真实分布标签
    y_true = []  
     
    # 从第i个高斯分布生成样本
    for i in range(n_components): 
        #生成多元正态分布样本
        X_i = np.random.multivariate_normal(mu_true[i], sigma_true[i], samples_per_component[i])
        # 将生成的样本添加到列表
        X_list.append(X_i) 
        # 添加对应标签
        y_true.extend([i] * samples_per_component[i]) 
     
    # 合并并打乱数据
    # 将多个子数据集合并为一个完整数据集
    X = np.vstack(X_list)  
    # 将Python列表转换为NumPy数组
    y_true = np.array(y_true) 
    # 生成0到n_samples-1的随机排列
    shuffle_idx = np.random.permutation(n_samples) 
    # 使用相同的随机索引同时打乱特征和标签
    return X[shuffle_idx], y_true[shuffle_idx]
 
# 自定义logsumexp函数
def logsumexp(log_p, axis=1, keepdims=False):
    """优化后的logsumexp实现，包含数值稳定性增强和特殊case处理
     
    计算log(sum(exp(log_p)))，通过减去最大值避免数值溢出
    数学公式: log(sum(exp(log_p))) = max(log_p) + log(sum(exp(log_p - max(log_p))))
    """
    log_p = np.asarray(log_p)   # 将对数概率列表转换为NumPy数组
     
    # 处理空输入情况
    if log_p.size == 0:  # 检查输入的对数概率数组是否为空
        return np.array(-np.inf, dtype=log_p.dtype)  # 返回与输入相同数据类型的负无穷值
     
    # 计算最大值（处理全-inf输入）
    max_val = np.max(log_p, axis=axis, keepdims=True)  # 计算沿指定轴的最大值
    if np.all(np.isneginf(max_val)):  # 检查是否所有最大值都是负无穷
        return max_val.copy() if keepdims else max_val.squeeze(axis=axis)  # 根据keepdims返回适当形式
     
    # 计算修正后的指数和（处理-inf输入）
    safe_log_p = np.where(np.isneginf(log_p), -np.inf, log_p - max_val)  # 安全调整对数概率
    sum_exp = np.sum(np.exp(safe_log_p), axis=axis, keepdims=keepdims)  # 计算调整后的指数和
     
    # 计算最终结果
    result = max_val + np.log(sum_exp)
     
    # 处理全-inf输入的特殊case
    if np.any(np.isneginf(log_p)) and not np.any(np.isfinite(log_p)):  # 判断是否所有有效值都是-inf
        result = max_val.copy() if keepdims else max_val.squeeze(axis=axis) # 根据keepdims参数的值返回max_val的适当形式
    return result  # 返回处理后的结果，保持与正常情况相同的接口
 
# 高斯混合模型类
class GaussianMixtureModel:
    """高斯混合模型(GMM)实现
     
    参数:
        n_components: int, 高斯分布数量 (默认=3)
        max_iter: int, EM算法最大迭代次数 (默认=100)
        tol: float, 收敛阈值 (默认=1e-6)
        random_state: int, 随机种子 (可选)
    """
    def __init__(self, n_components=3, max_iter=100, tol=1e-6 tol=1e-6, random_state=None):
        # 初始化模型参数
        self.n_components = n_components  # 高斯分布数量
        self.max_iter = max_iter          # EM算法最大迭代次数
        self.tol = tol                    # 收敛阈值
        self.log_likelihoods = []         #存储每轮迭代的对数似然值
 
        # 初始化随机数生成器
        self.rng = np.random.default_rng(random_state)
 
    def fit(self, X):
        """使用EM算法训练模型
 
        EM算法流程：
        1. 初始化模型参数（混合权重π、均值μ、协方差矩阵Σ）
        2. 重复以下步骤直到收敛：
           - E步：计算每个样本属于各高斯成分的后验概率（责任度）
           - M步：基于后验概率更新模型参数
        """
        X = np.asarray(X)
        n_samples, n_features = X.shape
         
        # 初始化混合系数（均匀分布）
        self.pi = np.ones(self.n_components) / self.n_components
         
        # 随机选择样本点作为初始均值
        self.mu = X[np.random.choice(n_samples, self.n_components, replace=False)]
         
        # 初始化协方差矩阵为单位矩阵
        self.sigma = np.array([np.eye(n_features) for _ in range(self.n_components)])
 
        log_likelihood = -np.inf  # 初始化对数似然值为负无穷
         
        # EM算法主循环：交替执行E步(期望)和M步(最大化)
        for iter in range(self.max_iter):
            # E步：计算后验概率（每个样本属于各个高斯成分的概率）
            log_prob = np.zeros((n_samples, self.n_components)) # 初始化对数概率矩阵
             
            # 对每个高斯成分，计算样本的对数概率密度
            for k in range(self.n_components):
                # 对数概率 = log(混合权重) + log(高斯概率密度)
                log_prob[:, k] = np.log(self.pi[k]) + self._log_gaussian(X, self.mu[k], self.sigma[k])
             
            # 使用logsumexp计算归一化因子，确保数值稳定性
            log_prob_sum = logsumexp(log_prob, axis=1, keepdims=True)
             
            # 计算后验概率（responsibility）：gamma_{ik} = P(z_i=k|x_i)
            gamma = np.exp(log_prob - log_prob_sum)
 
            # M步：更新模型参数（基于后验概率）
            Nk = np.sum(gamma, axis=0) # 每个高斯成分的"有效样本数"
             
            # 更新混合权重
            self.pi = Nk / n_samples
             
            # 初始化新均值和新协方差矩阵
            new_mu = np.zeros_like(self.mu)
            new_sigma = np.zeros_like(self.sigma)
 
            # 对每个高斯成分更新参数
            for k in range(self.n_components):
                # 更新均值：加权平均
                new_mu[k] = np.sum(gamma[:, k, None] * X, axis=0) / Nk[k]
 
                # 更新协方差矩阵
                X_centered = X - new_mu[k]  # 中心化数据
                weighted_X = gamma[:, k, None] * X_centered  # 加权中心化数据
                 
                # 使用einsum高效计算协方差矩阵
                # 等价于: new_sigma_k = (X_centered.T @ diag(gamma[:,k]) @ X_centered) / Nk[k]
                new_sigma_k = np.einsum('ni,nj->ij', X_centered, weighted_X) / Nk[k]
                 
                # 正则化：添加小的对角矩阵，防止协方差矩阵奇异
                eps = 1e-6  # 正则化系数
                new_sigma_k += np.eye(n_features) * eps
                 
                new_sigma[k] = new_sigma_k
 
            # 计算对数似然（模型对数据的拟合程度）
            current_log_likelihood = np.sum(log_prob_sum)  # 所有样本的对数似然之和
            self.log_likelihoods.append(current_log_likelihood)  # 记录当前对数似然
             
            # 检查收敛条件：如果对数似然变化小于阈值，则停止迭代
            if iter > 0 and abs(current_log_likelihood - log_likelihood) < self.tol:
                break
                 
            log_likelihood = current_log_likelihood
             
            # 更新模型参数
            self.mu = new_mu
            self.sigma = new_sigma
         
        # 最终聚类结果：每个样本分配到概率最大的高斯成分
        self.labels_ = np.argmax(gamma, axis=1)
        return self
 
    def _log_gaussian(self, X, mu, sigma):
        """计算多维高斯分布的对数概率密度
         
        参数:
            X: 输入数据，shape=(n_samples, n_features)
            mu: 高斯分布均值，shape=(n_features,)
            sigma: 高斯分布协方差矩阵，shape=(n_features, n_features)
             
        返回:
            log_prob: 对数概率密度，shape=(n_samples,)
        """
        # 获取特征维度数量
        n_features = mu.shape[0]
 
        # 数据中心化：每个样本减去均值
        X_centered = X - mu
 
        # 计算协方差矩阵的对数行列式和逆矩阵
        # 行列式用于计算高斯分布的归一化常数
        sign, logdet = np.linalg.slogdet(sigma)
         
        # 处理协方差矩阵接近奇异的情况（行列式接近0）
        if sign <= 0:
            # 添加微小扰动确保协方差矩阵正定（数值稳定性）
            sigma += np.eye(n_features) * 1e-6
            sign, logdet = np.linalg.slogdet(sigma)
 
        # 计算协方差矩阵的逆
        inv = np.linalg.inv(sigma)
         
        # 计算二次型：(x-μ)^T·Σ^(-1)·(x-μ)
        # 使用einsum高效计算多个样本的二次型
        exponent = -0.5 * np.einsum('...i,...i->...', X_centered @ inv, X_centered)
 
        # 返回对数概率密度
        # 公式：log_p(x) = -0.5*D*log(2π) - 0.5*log|Σ| - 0.5*(x-μ)^T·Σ^(-1)·(x-μ)
        return -0.5 * n_features * np.log(2 * np.pi) - 0.5 * logdet + exponent
     
    def plot_convergence(self):
        """可视化对数似然的收敛过程"""
        # 检查是否有对数似然值记录
        if not self.log_likelihoods:
            raise ValueError("请先调用fit方法训练模型")
 
        # 创建一个图形窗口，设置大小为10x6英寸
        plt.figure(figsize=(10, 6))
        # 绘制对数似然值随迭代次数的变化曲线
        # 使用蓝色实线绘制，范围从1到len(self.log_likelihoods)
        plt.plot(range(1, len(self.log_likelihoods) + 1), self.log_likelihoods, 'b-')
        # 设置x轴标签为“迭代次数”
        plt.xlabel('迭代次数')
        # 设置y轴标签为“对数似然值”
        plt.ylabel('对数似然值')
        # 设置图表标题为“EM算法收敛曲线”
        plt.title('EM算法收敛曲线')
        # 启用网格线，增强可读性
        plt.grid(True)  
        plt.show()
 
# 主程序
if __name__ == "__main__":
    # 1. 生成合成数据
    print("生成混合高斯分布数据...")
    X, y_true = generate_data(n_samples=1000)
    print(f"生成数据形状: {X.shape}, 标签形状: {y_true.shape}")
     
    # 2. 训练GMM模型
    print("\n训练高斯混合模型...")
    gmm = GaussianMixtureModel(n_components=3, random_state=42)
    gmm.fit(X)
    y_pred = gmm.labels_
    print(f"完成训练，共进行{len(gmm.log_likelihoods)}次迭代")
     
    # 3. 可视化收敛过程
    print("\n绘制EM算法收敛曲线...")
    gmm.plot_convergence()
     
    # 4. 可视化聚类结果
    print("\n可视化聚类结果...")
    plt.figure(figsize=(12, 5))
     
    # 左图：真实聚类
    plt.subplot(1, 2, 1)
    plt.scatter(X[:, 0], X[:, 1], c=y_true, cmap='viridis', s=15, alpha=0.8)
    plt.title("真实聚类", fontsize=12)
    plt.xlabel("特征1", fontsize=10)
    plt.ylabel("特征2", fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
     
    # 右图：GMM预测聚类
    plt.subplot(1, 2, 2)
    plt.scatter(X[:, 0], X[:, 1], c=y_pred, cmap='viridis', s=15, alpha=0.8)
    plt.title("GMM预测聚类", fontsize=12)
    plt.xlabel("特征1", fontsize=10)
    plt.ylabel("特征2", fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
     
    plt.tight_layout()
    plt.savefig('gmm_clustering_results.png', dpi=300)
    plt.show()
    print("程序执行完毕")
