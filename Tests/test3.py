# 可视化检查
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import re

ocr_result = [
    {'text': '犀牛', 'confidence': 0.9983408451080322, 'box': [[161, 164], [190, 161], [192, 179], [164, 182]], 'center': [176, 171]},
    {'text': '犀牛', 'confidence': 0.9894095659255981, 'box': [[547, 163], [575, 163], [575, 182], [547, 182]], 'center': [561, 172]},
    {'text': '犀牛，', 'confidence': 0.996931254863739, 'box': [[547, 199], [592, 199], [592, 217], [547, 217]], 'center': [569, 208]},
    {'text': '·犀牛', 'confidence': 0.8275837898254395, 'box': [[679, 197], [719, 200], [718, 218], [678, 216]], 'center': [698, 207]},
    {'text': '犀牛', 'confidence': 0.9796620607376099, 'box': [[499, 235], [528, 235], [528, 254], [499, 254]], 'center': [513, 244]},
    {'text': '犀牛', 'confidence': 0.9974762201309204, 'box': [[595, 235], [624, 235], [624, 253], [595, 253]], 'center': [609, 244]},
    {'text': '‘犀牛', 'confidence': 0.8513173460960388, 'box': [[637, 236], [671, 236], [671, 253], [637, 253]], 'center': [654, 244]},
    {'text': '侠众道犀牛', 'confidence': 0.9993091821670532, 'box': [[492, 306], [575, 306], [575, 326], [492, 326]], 'center': [533, 316]},
    {'text': '犀牛', 'confidence': 0.9929553270339966, 'box': [[643, 307], [670, 307], [670, 326], [643, 326]], 'center': [656, 316]},
    {'text': '犀牛。', 'confidence': 0.9311910271644592, 'box': [[547, 343], [580, 343], [580, 363], [547, 363]], 'center': [563, 353]},
    {'text': '犀牛', 'confidence': 0.9894095659255981, 'box': [[259, 379], [287, 379], [287, 398], [259, 398]], 'center': [273, 388]},
    {'text': '犀牛', 'confidence': 0.9959057569503784, 'box': [[354, 379], [384, 379], [384, 398], [354, 398]], 'center': [369, 388]},
    {'text': '犀牛', 'confidence': 0.9850710034370422, 'box': [[499, 379], [528, 379], [528, 398], [499, 398]], 'center': [513, 388]},
    {'text': '犀牛', 'confidence': 0.9894095659255981, 'box': [[499, 415], [527, 415], [527, 434], [499, 434]], 'center': [513, 424]},
    {'text': '犀牛', 'confidence': 0.9939484596252441, 'box': [[595, 522], [623, 522], [623, 542], [595, 542]], 'center': [609, 532]},
    {'text': '犀牛', 'confidence': 0.99814772605896, 'box': [[595, 560], [625, 560], [625, 577], [595, 577]], 'center': [610, 568]},
    {'text': '犀牛', 'confidence': 0.9995726346969604, 'box': [[641, 560], [684, 560], [684, 576], [641, 576]], 'center': [662, 568]}
]




def get_bounding_box(box):
    x_coords = [point[0] for point in box]
    y_coords = [point[1] for point in box]
    x_min = min(x_coords)
    x_max = max(x_coords)
    y_min = min(y_coords)
    y_max = max(y_coords)
    return {
        'x_min': x_min,
        'x_max': x_max,
        'y_min': y_min,
        'y_max': y_max,
        'width': x_max - x_min,
        'height': y_max - y_min
    }

def expected_width(text, char_width=11.5):
    return len(text) * char_width

def should_split(actual_width, expected_width, text, threshold=3):
    return abs(actual_width - expected_width) > threshold and len(text) > 1

def split_box(box, text, num_parts, confidence):
    width = box['x_max'] - box['x_min']
    part_width = width / num_parts
    boxes = []
    for i in range(num_parts):
        x_min = box['x_min'] + i * part_width
        x_max = box['x_min'] + (i + 1) * part_width
        # 生成四个点的box
        new_box = [
            [x_min, box['y_min']],
            [x_max, box['y_min']],
            [x_max, box['y_max']],
            [x_min, box['y_max']]
        ]
        new_item = {
            'text': text[i],
            'confidence': confidence,
            'box': new_box,
            'center': [(x_min + x_max) / 2, (box['y_min'] + box['y_max']) / 2]
        }
        boxes.append(new_item)
    return boxes

def clean_text(text):
    # 使用正则表达式去除无用的标点符号
    return re.sub(r'[^\w\s]', '', text)

final_ocr_result = []
for item in ocr_result:
    cleaned_text = clean_text(item['text'])
    box_info = get_bounding_box(item['box'])
    expected_w = expected_width(cleaned_text)
    if should_split(box_info['width'], expected_w, cleaned_text):
        num_parts = len(cleaned_text)
        split_boxes = split_box(box_info, cleaned_text, num_parts, item['confidence'])
        final_ocr_result.extend(split_boxes)
    else:
        final_ocr_result.append({
            'text': cleaned_text,
            'confidence': item['confidence'],
            'box': item['box'],
            'center': item['center']
        })

# 打印处理后的OCR结果
print("开始处理OCR结果...")
for item in final_ocr_result:
    print(item)
print("OCR结果处理完毕。")

def calculate_distance(center1, center2):
    return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5

def combine_boxes(boxes):
    if not boxes:
        return None
    x_min = min(box['box'][0][0] for box in boxes)
    x_max = max(box['box'][1][0] for box in boxes)
    y_min = min(box['box'][0][1] for box in boxes)
    y_max = max(box['box'][2][1] for box in boxes)
    combined_text = ''.join(box['text'] for box in boxes)
    combined_center = [(x_min + x_max) / 2, (y_min + y_max) / 2]
    return {
        'text': combined_text,
        'confidence': min(box['confidence'] for box in boxes),  # 取最小置信度
        'box': [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]],
        'center': combined_center
    }

# 组合相邻字符成词组
grouped_ocr_result = []
temp_group = []

for i, item in enumerate(final_ocr_result):
    if temp_group:
        last_item = temp_group[-1]
        distance = calculate_distance(last_item['center'], item['center'])
        if distance > 16:
            grouped_ocr_result.append(combine_boxes(temp_group))
            temp_group = []
    temp_group.append(item)

# 添加最后一个组
if temp_group:
    grouped_ocr_result.append(combine_boxes(temp_group))

# 打印组合后的OCR结果
print("组合后的OCR结果:")
for item in grouped_ocr_result:
    print(item)


