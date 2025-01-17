import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging


class ImagePreprocessor:
    """图像预处理类"""
    MODULE_NAME = 'ImagePreprocessor'
    
    def __init__(self, basic_config: dict, area_config: dict, logger: logging.Logger):
        """初始化图像预处理器
        
        Args:
            basic_config: 基础配置字典
            logger: 日志实例
        """
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<图像预处理器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config
        self.area_config = area_config
        self.base_output_dir = Path(basic_config.get('base_output_dir', 'output'))
        self.preprocessed_dir = self.base_output_dir / basic_config.get('preprocessed_dir', 'preprocessed')   
        # 针对具体区域名称的预处理方法映射
        self.region_specific_methods = {
            'title_area': self._preprocess_title_area,  # 标题区域
            'game_area': self._preprocess_game_area,  # 游戏区域 
            'char_vitality': self._preprocess_char_vitality,  # 角色活力值
            'char_neigong': self._preprocess_neigong_area,  # 角色内功值
            'char_head': self._preprocess_char_defense,  # 角色头防值
            'char_hand': self._preprocess_char_defense,  # 角色手防值
            'char_foot': self._preprocess_char_defense,  # 角色脚防值  
            'char_qigong': self._preprocess_char_defense,  # 角色元气值 
            'skill_exp_min': self._preprocess_skill_exp,  # 技能小经验值
            'skill_exp_max': self._preprocess_skill_exp,  # 技能大经验值
            'target_hp': self._preprocess_target_hp,  # 目标血量
            'nearby_monster_name_1': self._preprocess_nearby_monster_name_1,  # 近身寻怪名区域-1
            'nearby_monster_name_2': self._preprocess_nearby_monster_name_1,  # 近身寻怪名区域-2
            'char_revival': self._preprocess_char_revival,  # 角色复活信息
            'char_eat_food': self._preprocess_char_revival,  # 角色食物状态
            'char_be_attack': self._preprocess_char_be_attack,  # 角色被攻击状态
            'char_blood_loss': self._preprocess_char_blood_loss,  # 角色掉血值
            # 可以继续添加更多区域特定的处理方法...
        }
        self.logger.info("=========================图像预处理器初始化完成=========================    ")

    # 角色掉血值预处理
    def _preprocess_char_blood_loss(self, image: np.ndarray) -> np.ndarray:
        """角色掉血值预处理"""
        try:
            # 定义目标颜色 (BGR格式)
            target_color = np.array([0, 0, 255])  # OpenCV中是BGR顺序
            # 定义颜色容差
            tolerance = 5
            
            # 创建颜色掩码
            lower_bound = target_color - tolerance
            upper_bound = target_color + tolerance
            mask = cv2.inRange(image, lower_bound, upper_bound)
            
            # 创建全白图像
            result = np.ones_like(image) * 255
            
            # 将掩码区域设为黑色
            result[mask > 0] = [0, 0, 0]
            
            # 转换为灰度图
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            
            # 二值化处理
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # 获取原始图像的尺寸
            original_height, original_width = binary.shape[:2]

            # 定义放大比例
            scale_factor = 4.0  # 例如，放大2倍

            # 计算新的尺寸
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)

            # 使用cv2.resize()进行图像放大
            resized_image = cv2.resize(binary, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

            return resized_image
            
        except Exception as e:
            self.logger.error(f"预处理角色掉血值图像出错: {str(e)}")
            return image

    # 角色被攻击状态预处理
    def _preprocess_char_be_attack(self, image: np.ndarray) -> np.ndarray:
        """角色被攻击状态预处理
        处理图片，只保留特定颜色(R=176, G=40, B=40)并转换为黑白图
        """
        try:
            # 定义目标颜色 (BGR格式)
            target_color = np.array([40, 40, 176])  # OpenCV中是BGR顺序
            # 定义颜色容差
            tolerance = 5
            
            # 创建颜色掩码
            lower_bound = target_color - tolerance
            upper_bound = target_color + tolerance
            mask = cv2.inRange(image, lower_bound, upper_bound)
            
            # 创建全白图像
            result = np.ones_like(image) * 255
            
            # 将掩码区域设为黑色
            result[mask > 0] = [0, 0, 0]
            
            # 转换为灰度图
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            
            # 二值化处理
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            return binary
            
        except Exception as e:
            self.logger.error(f"预处理角色被攻击状态图像出错: {str(e)}")
            return image
    
    # 角色复活信息预处理
    def _preprocess_char_revival(self, image: np.ndarray) -> np.ndarray:
        """
        角色复活信息预处理
        """
        # 增强对比度
        alpha = 1.3
        beta = 0
        enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

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
        # 反转图像
        cleaned_mask = cv2.bitwise_not(cleaned_mask)    
        return cleaned_mask
    
    # 近身寻怪名区域-1
    def _preprocess_nearby_monster_name_1(self, image: np.ndarray) -> np.ndarray:
        """
        近身寻怪名区域-1预处理
        """
        # 获取图像尺寸
        height, width = image.shape[:2]

        # 创建掩码（全白色）
        mask = np.ones_like(image) * 255

        # 在垂直方向上按规律填充黑色遮罩
        y = 16  # 从第16行开始
        while y < height:
            # 填充20行
            if y + 20 <= height:
                pts = np.array([[0, y], [0, y+20], [width, y+20], [width, y]])
                cv2.fillPoly(mask, [pts], (0, 0, 0))
            y += 36  # 跳到下一个填充起点(20+16=36)

        # 第二个固定区域的填充
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

        # 反转图像
        image = cv2.bitwise_not(masked_image)
        # -------------------------------------------------------------------------------------------
        # 将图像从 BGR 转换为 HSV 颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 定义红色的范围（HSV 颜色空间）
        lower_red = np.array([0, 50, 50])  # 红色的下限
        upper_red = np.array([10, 255, 255])  # 红色的上限

        # 创建一个掩码，标记红色区域    *蓝色文字也变黑色
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        # 创建一个掩码，标记 R=255 且 B=255 的区域    *绿色文字也变黑色
        rb_mask = (image[:, :, 0] >= 255) & (image[:, :, 2] >= 255) & (image[:, :, 1] < 10)     # 绿色文字也变黑色
        # 将红色区域和 R=255 且 B=255 的区域填充为黑色
        image[red_mask == 255] = [0, 0, 0]      # 红色区域
        image[rb_mask] = [0, 0, 0]              # R=255 且 B=255 的区域

        # 将图像转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 二值化处理（阈值为 15）
        _, binary = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
        
        return binary
    
    # 目标血量预处理
    def _preprocess_target_hp(self, image: np.ndarray) -> np.ndarray:
        """
        目标血量预处理
        
        处理步骤:
        1. 增强对比度
        2. 转换到HSV颜色空间
        3. 创建红色掩码(包括多个红色范围)
        4. 应用形态学操作
        5. 处理采样区域
        6. 反转图像
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 处理后的二值图像
        """
        # 增强对比度
        alpha = 1.3
        beta = 0
        image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        # 转换到HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 原有的红色范围(注释但保留)
        """
        # 定义红色的HSV范围
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        # 创建红色掩码
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2
        """

        # 新增的红色范围(包括R值59和39的情况)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        # 新增的红色范围
        lower_red3 = np.array([0, 50, 50])  # 适配较暗的红色(R=59)
        upper_red3 = np.array([10, 255, 255])
        lower_red4 = np.array([0, 30, 30])  # 适配更暗的红色(R=39)
        upper_red4 = np.array([10, 255, 255])

        # 创建红色掩码(包含所有范围)
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask3 = cv2.inRange(hsv, lower_red3, upper_red3)
        mask4 = cv2.inRange(hsv, lower_red4, upper_red4)
        red_mask = mask1 + mask2 + mask3 + mask4

        # 应用形态学操作
        kernel = np.ones((3,3), np.uint8)
        red_mask = cv2.dilate(red_mask, kernel, iterations=1)
        red_mask = cv2.erode(red_mask, kernel, iterations=1)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

        # 获取图像尺寸
        height, width = red_mask.shape
        center_y = height // 2
        sample_height = height
        start_y = center_y - sample_height//2
        end_y = center_y + sample_height//2

        # 创建最终的二值图
        binary = np.zeros_like(red_mask)
        # 只保留采样区域内的有效像素
        for x in range(width):
            column = red_mask[start_y:end_y, x]
            if np.any(column > 0):
                binary[start_y:end_y, x] = 255

        # 反转图片颜色
        binary = cv2.bitwise_not(binary)

        return binary
       
    # 技能经验预处理
    def _preprocess_skill_exp(self, image: np.ndarray) -> np.ndarray:
        """
        技能经验预处理
        """
        # 设置对比度为最大
        alpha = 2  # 对比度系数
        beta = 0     # 亮度调整
        # 转换为灰度图
        gray = cv2.cvtColor(cv2.convertScaleAbs(image, alpha=alpha, beta=beta), cv2.COLOR_BGR2GRAY)
        # 二值化处理
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        # 反转图片颜色
        binary = cv2.bitwise_not(binary)
        return binary 

    # 角色防值预处理
    def _preprocess_char_defense(self, image: np.ndarray) -> np.ndarray:
        """
        角色防值预处理
        """
        # 设置对比度为最大
        alpha = 2  # 对比度系数
        beta = 0     # 亮度调整
        # 转换为灰度图
        gray = cv2.cvtColor(cv2.convertScaleAbs(image, alpha=alpha, beta=beta), cv2.COLOR_BGR2GRAY)
        # 二值化处理
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        # 反转图片颜色
        binary = cv2.bitwise_not(binary)
        return binary   
    
    # 角色内功值预处理
    def _preprocess_neigong_area(self, image: np.ndarray) -> np.ndarray:
        """
        角色内功值预处理
        """
        # 设置对比度为最大
        alpha = 2  # 对比度系数
        beta = 0     # 亮度调整
        # 转换为灰度图
        gray = cv2.cvtColor(cv2.convertScaleAbs(image, alpha=alpha, beta=beta), cv2.COLOR_BGR2GRAY)
        # 步骤2：二值化处理
        _, binary = cv2.threshold(gray, 76, 255, cv2.THRESH_BINARY)

        # 反转图片颜色
        binary = cv2.bitwise_not(binary)

        return binary
    
    # 角色活力值预处理
    def _preprocess_char_vitality(self, image: np.ndarray) -> np.ndarray:
        """
        角色活力值预处理
        """

        # 设置对比度为最大
        alpha = 2  # 对比度系数
        beta = 0     # 亮度调整
        # 转换为灰度图
        gray = cv2.cvtColor(cv2.convertScaleAbs(image, alpha=alpha, beta=beta), cv2.COLOR_BGR2GRAY)
        # 步骤2：二值化处理
        _, binary = cv2.threshold(gray, 76, 255, cv2.THRESH_BINARY)

        # 反转图片颜色
        binary = cv2.bitwise_not(binary)

        return binary
    
    # 游戏区域预处理
    def _preprocess_game_area(self, image: np.ndarray) -> np.ndarray:
        """
        为图像添加遮罩并显示结果。

        参数:
            mask_height (int): 遮罩的高度（默认 20 像素）。
            spacing (int): 遮罩之间的间隔（默认 16 像素）。
        """
        # 遮罩参数
        mask_height=20
        spacing=16

        # 获取图像的高度和宽度
        height, width = image.shape[:2]

        # 创建一个纯黑色的遮罩
        mask = np.zeros((mask_height, width, 3), dtype=np.uint8)  # 3 通道（BGR）

        # 在图像上添加第一个遮罩（水平条纹）
        y = 0
        while y < height:
            # 添加遮罩
            if y + mask_height <= height:
                image[y:y + mask_height, 0:width] = mask
            else:
                # 如果剩余高度不足，只填充剩余部分
                image[y:height, 0:width] = mask[:height - y, :]         
            # 更新 y 坐标，跳过间隔
            y += mask_height + spacing

        # 定义多个遮罩区域的坐标
        mask_regions = [
            (0, 10, 960, 122),  # 第一个矩形区域
            (0, 0, width, 127),   # 第二个矩形区域
            (10, 322, 191, 364),   # 第三个矩形区域
            (20, 139, 116, 200),    # 第四个矩形区域
        ]
        
        # 添加多个遮罩区域
        for region in mask_regions:
            x1, y1, x2, y2 = region
            image[y1:y2, x1:x2] = 0  # 将指定区域填充为纯黑色
        # 反转图像
        image = cv2.bitwise_not(image)
        # -------------------------------------------------------------------------------------------
        # 将图像从 BGR 转换为 HSV 颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 定义红色的范围（HSV 颜色空间）
        lower_red = np.array([0, 50, 50])  # 红色的下限
        upper_red = np.array([10, 255, 255])  # 红色的上限

        # 创建一个掩码，标记红色区域    *蓝色文字也变黑色
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        # 创建一个掩码，标记 R=255 且 B=255 的区域    *绿色文字也变黑色
        rb_mask = (image[:, :, 0] >= 255) & (image[:, :, 2] >= 255) & (image[:, :, 1] < 10)     # 绿色文字也变黑色
        # 将红色区域和 R=255 且 B=255 的区域填充为黑色
        image[red_mask == 255] = [0, 0, 0]      # 红色区域
        image[rb_mask] = [0, 0, 0]              # R=255 且 B=255 的区域

        # 将图像转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 二值化处理（阈值为 15）
        _, binary = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)

        return binary
    # 预处理标题区域
    def _preprocess_title_area(self, image: np.ndarray) -> np.ndarray:
        """标题区域预处理"""
        # 转换为灰度图并进行自适应二值化
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 二值化
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    # 显示调试窗口
    def show_debug_window(self, region_name: str, image: np.ndarray) -> None:
        """显示调试窗口
        
        Args:
            region_name: 区域名称
            image: 要显示的图像
        """
        window_name = f"Preprocessed-{region_name}"
        cv2.imshow(window_name, image)
        # 非阻塞方式检查按键，如果按下'q'则关闭所有窗口
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
    # 处理多个区域的图像
    def process_images(self,
                      images: Dict[str, np.ndarray],
                      regions_to_process: Optional[List[str]] = None,
                      debug_mode: bool = False,
                      save_debug: bool = False,
                      timestamp: str = None) -> Dict[str, np.ndarray]:
        """处理多个区域的图像"""
        processed_images = {}
        
        if regions_to_process is None:
            regions_to_process = list(images.keys())
        
        for region_name in regions_to_process:
            if region_name not in images:
                continue
                
            # 获取区域配置
            region_config = self.area_config.get(region_name, {})

            # 获取处理方法
            preprocess_method = self.region_specific_methods.get(region_name)
            if not preprocess_method:
                self.logger.debug(f"区域 {region_name} 无特定处理方法，返回原图")
                processed_images[region_name] = images[region_name].copy()
                continue
            
            # 预处理图像
            processed_image = preprocess_method(images[region_name])
            processed_images[region_name] = processed_image

            # 保存调试图像
            if save_debug and timestamp:
                try:
                    region_dir = self.preprocessed_dir / region_name
                    region_dir.mkdir(parents=True, exist_ok=True)
                    save_path = region_dir / f"{timestamp}.png"
                    cv2.imwrite(str(save_path), processed_image)
                    self.logger.debug(f"已保存预处理图像: {save_path}")
                except Exception as e:
                    self.logger.error(f"保存预处理图像失败: {e}")

        # 如果开启了调试模式，显示所有处理后的图像
        if debug_mode:
            while True:
                # 显示所有处理后的图像
                for region_name, image in processed_images.items():
                    cv2.imshow(f"Preprocessed-{region_name}", image)
                
                # 检查是否按下 'q' 键
                if cv2.waitKey(100) & 0xFF == ord('q'):  # 增加等待时间到100ms
                    cv2.destroyAllWindows()
                    break

        return processed_images

    def __del__(self):
        """析构函数：清理所有窗口"""
        cv2.destroyAllWindows() 