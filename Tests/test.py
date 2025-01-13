import cv2
import numpy as np

def fill_red_and_blue_with_black(image_path):
    """
    将图像中的红色区域和 R=255 且 B=255 的区域填充为纯黑色。

    参数:
        image_path (str): 输入图像的路径。

    返回:
        np.ndarray: 处理后的图像。
    """
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("无法读取图像，请检查图像路径是否正确。")
    # 反转图像
    image = cv2.bitwise_not(image)
    # 将图像从 BGR 转换为 HSV 颜色空间
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 定义红色的范围（HSV 颜色空间）
    lower_red = np.array([0, 50, 50])  # 红色的下限
    upper_red = np.array([10, 255, 255])  # 红色的上限

    # 创建一个掩码，标记红色区域
    red_mask = cv2.inRange(hsv, lower_red, upper_red)

    # 创建一个掩码，标记 R=255 且 B=255 的区域
    rb_mask = (image[:, :, 0] >= 255) & (image[:, :, 2] >= 255) & (image[:, :, 1] < 10)


    # 将红色区域和 R=255 且 B=255 的区域填充为黑色
    image[red_mask == 255] = [0, 0, 0]  # 红色区域
    image[rb_mask] = [0, 0, 0]  # R=255 且 B=255 的区域

    # 显示处理后的图像
    cv2.imshow("Processed Image", image)
    cv2.waitKey(0)  # 等待按键
    cv2.destroyAllWindows()  # 关闭窗口

    return image

# 示例调用
input_image_path = r"A:\1000Y_DATA_TEMP\data\original_screenshots\game_area\game_area_1736624839_1327827.png"  # 输入图像路径
try:
    processed_image = fill_red_and_blue_with_black(input_image_path)
except Exception as e:
    print(f"发生错误: {e}")





    