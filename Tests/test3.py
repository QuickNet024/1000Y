import cv2
import numpy as np

# 读取测试图片
image_path = "B:/1000Y_DATA_TEMP/data/original/char_revival/1737037824_4415081.png"
original_image = cv2.imread(image_path)

if original_image is None:
    print("错误: 无法读取图片")
    exit()

# 增强对比度
alpha = 1.3
beta = 0
enhanced = cv2.convertScaleAbs(original_image, alpha=alpha, beta=beta)

# 转换到HSV颜色空间
hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)

# 定义黄色的HSV范围（调整更精确的范围）
lower_yellow = np.array([20, 130, 130])  # 稍微降低饱和度和亮度的下限
upper_yellow = np.array([30, 255, 255])

# 创建黄色掩码
yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

# 去除小面积的噪点
# 1. 先进行连通区域分析
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(yellow_mask, connectivity=8)

# 2. 创建新的掩码，只保留面积大于阈值的区域
min_area = 1  # 减小最小面积阈值，保留文字中的点
cleaned_mask = np.zeros_like(yellow_mask)
for i in range(1, num_labels):  # 从1开始，跳过背景
    if stats[i, cv2.CC_STAT_AREA] >= min_area:
        cleaned_mask[labels == i] = 255

# 显示结果
scale = 4  # 放大倍数
enlarged_original = cv2.resize(original_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
enlarged_mask = cv2.resize(cleaned_mask, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

cv2.imshow("1-原始图片", enlarged_original)
cv2.imshow("2-黄色文字提取", enlarged_mask)
cv2.waitKey(0)
cv2.destroyAllWindows()
