import cv2
import numpy as np
from pathlib import Path

def apply_mask_to_image(image_path):
    """
    读取图片并应用遮罩
    
    Args:
        image_path: 图片路径
    """
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        print("无法读取图片，请检查路径")
        return

    # 获取图像尺寸
    height, width = image.shape[:2]

    # 创建掩码（全白色）
    mask = np.ones_like(image) * 255

    # 在垂直方向上按规律填充黑色遮罩
    # 0-15行不填充
    # 16-35行填充（20像素高度）
    # 36-51行不填充（16像素高度）
    # 52-71行填充（20像素高度）
    # 72-87行不填充（16像素高度）
    # 以此类推...
    y = 16  # 从第16行开始
    while y < height:
        # 填充20行
        if y + 20 <= height:
            pts = np.array([[0, y], [0, y+20], [width, y+20], [width, y]])
            cv2.fillPoly(mask, [pts], (0, 0, 0))
        y += 36  # 跳到下一个填充起点(20+16=36)

    # 计算图片中心位置
    center_x = width // 2
    center_y = height // 2
    
    # 计算第二个遮罩区域的坐标
    # 上下高度为16px，总宽度为42px
    mask_half_height = 8  # 16/2
    mask_half_width = 21  # 42/2
    
    # 计算遮罩区域的四个角点
    pts2 = np.array([
        [center_x - mask_half_width, center_y - mask_half_height],  # 左上
        [center_x - mask_half_width, center_y + mask_half_height],  # 左下
        [center_x + mask_half_width, center_y + mask_half_height],  # 右下
        [center_x + mask_half_width, center_y - mask_half_height]   # 右上
    ])
    cv2.fillPoly(mask, [pts2], (0, 0, 0))

    # 将掩码应用到原图
    masked_image = cv2.bitwise_and(image, mask)

    # 显示结果
    scale = 4  # 放大倍数
    enlarged_original = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    enlarged_masked = cv2.resize(masked_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

    cv2.imshow("1原始图片", enlarged_original)
    cv2.imshow("2遮罩后的图片", enlarged_masked)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 测试代码
    image_path = "B:/1000Y_DATA_TEMP/data\original/nearby_monster_name_1/1736969195_9716730.png"
    apply_mask_to_image(image_path)
    