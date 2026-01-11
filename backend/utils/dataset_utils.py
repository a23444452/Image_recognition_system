"""
資料集處理工具
從 YOLO_No_Code_Training 遷移並改造
根據會議共識加入 ProcessPoolExecutor 優化
"""

import yaml
import os
import shutil
import random
import logging
from pathlib import Path
from typing import Optional, Callable, List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def create_data_yaml(
    train_path: str,
    val_path: str,
    class_names_str: str,
    output_path: str = "data.yaml"
) -> str:
    """
    生成 YOLO 訓練所需的 data.yaml 檔案

    Args:
        train_path: 訓練圖片路徑
        val_path: 驗證圖片路徑
        class_names_str: 逗號分隔的類別名稱字串
        output_path: 輸出檔案路徑

    Returns:
        str: 生成的 yaml 檔案絕對路徑
    """
    # 解析類別名稱
    classes = [c.strip() for c in class_names_str.split(',') if c.strip()]
    names_dict = {i: name for i, name in enumerate(classes)}

    # 若驗證路徑缺失，使用訓練路徑
    if not val_path:
        val_path = train_path
        logger.warning("驗證路徑缺失，使用訓練路徑")

    # 建立配置
    data = {
        'path': os.path.abspath(os.path.dirname(output_path)),
        'train': os.path.abspath(train_path),
        'val': os.path.abspath(val_path),
        'names': names_dict,
        'nc': len(classes)
    }

    # 寫入 yaml
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    logger.info(f"✅ 已生成 data.yaml: {output_path}")
    logger.info(f"   - {len(classes)} 個類別")

    return os.path.abspath(output_path)


def split_dataset(
    source_folder: str,
    output_folder: str,
    split_ratio: float = 0.8,
    progress_callback: Optional[Callable[[str], None]] = None,
    use_multiprocessing: bool = True,
    max_workers: int = 4
) -> Tuple[int, int]:
    """
    將原始資料集分割為 YOLO train/val 結構

    根據會議共識：使用 ProcessPoolExecutor 加速檔案複製

    Args:
        source_folder: 包含圖片和標註的原始資料夾
        output_folder: 目標資料夾
        split_ratio: 訓練集比例 (0.0 到 1.0)
        progress_callback: 進度回調函數
        use_multiprocessing: 是否使用多進程加速
        max_workers: 最大 worker 數量

    Returns:
        Tuple[int, int]: (訓練集圖片數, 驗證集圖片數)
    """
    source = Path(source_folder)
    dest = Path(output_folder)

    if not source.exists():
        raise FileNotFoundError(f"來源資料夾不存在: {source}")

    # 建立目錄結構
    (dest / 'images' / 'train').mkdir(parents=True, exist_ok=True)
    (dest / 'images' / 'val').mkdir(parents=True, exist_ok=True)
    (dest / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
    (dest / 'labels' / 'val').mkdir(parents=True, exist_ok=True)

    # 取得所有圖片
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    images = [f for f in source.iterdir() if f.suffix.lower() in valid_exts]

    if not images:
        msg = "來源資料夾中未找到圖片"
        logger.warning(msg)
        if progress_callback:
            progress_callback(msg)
        return 0, 0

    # 隨機打亂
    random.shuffle(images)

    # 分割
    split_idx = int(len(images) * split_ratio)
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]

    msg = f"📊 找到 {len(images)} 張圖片。分割: {len(train_imgs)} 訓練, {len(val_imgs)} 驗證"
    logger.info(msg)
    if progress_callback:
        progress_callback(msg)

    # 複製檔案函數
    def copy_file_pair(img_path: Path, dest_folder: Path, split_type: str):
        """複製圖片和對應的標註檔"""
        try:
            # 複製圖片
            shutil.copy2(img_path, dest_folder / 'images' / split_type / img_path.name)

            # 複製標註（若存在）
            label_path = img_path.with_suffix('.txt')
            if label_path.exists():
                shutil.copy2(label_path, dest_folder / 'labels' / split_type / label_path.name)

            return True
        except Exception as e:
            logger.error(f"複製失敗 {img_path.name}: {e}")
            return False

    # 複製檔案（使用多進程優化）
    if use_multiprocessing and len(images) > 100:
        msg = f"⚡ 使用 {max_workers} 個 worker 加速複製..."
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 訓練集
            train_futures = [
                executor.submit(copy_file_pair, img, dest, 'train')
                for img in train_imgs
            ]
            # 驗證集
            val_futures = [
                executor.submit(copy_file_pair, img, dest, 'val')
                for img in val_imgs
            ]

            # 等待完成
            for future in as_completed(train_futures + val_futures):
                future.result()
    else:
        # 單進程複製（小型資料集）
        for img in train_imgs:
            copy_file_pair(img, dest, 'train')
        for img in val_imgs:
            copy_file_pair(img, dest, 'val')

    # 處理 classes.txt
    classes_file = source / 'classes.txt'
    if classes_file.exists():
        shutil.copy2(classes_file, dest / 'classes.txt')
        msg = "✅ 已複製 classes.txt"
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)

    msg = f"✅ 資料集準備完成: {dest}"
    logger.info(msg)
    if progress_callback:
        progress_callback(msg)

    return len(train_imgs), len(val_imgs)


def validate_dataset(dataset_folder: str) -> dict:
    """
    驗證資料集結構與完整性

    Args:
        dataset_folder: 資料集資料夾路徑

    Returns:
        dict: 驗證結果
    """
    folder = Path(dataset_folder)
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }

    # 檢查目錄結構
    required_dirs = [
        'images/train',
        'images/val',
        'labels/train',
        'labels/val'
    ]

    for dir_path in required_dirs:
        if not (folder / dir_path).exists():
            result['valid'] = False
            result['errors'].append(f"缺少目錄: {dir_path}")

    if not result['valid']:
        return result

    # 統計圖片與標註
    for split in ['train', 'val']:
        img_dir = folder / 'images' / split
        label_dir = folder / 'labels' / split

        images = list(img_dir.glob('*.*'))
        labels = list(label_dir.glob('*.txt'))

        img_count = len(images)
        label_count = len(labels)

        result['stats'][split] = {
            'images': img_count,
            'labels': label_count
        }

        # 警告：標註數量不匹配
        if img_count != label_count:
            result['warnings'].append(
                f"{split} 集圖片數 ({img_count}) 與標註數 ({label_count}) 不匹配"
            )

    logger.info(f"資料集驗證完成: {result}")
    return result


def get_dataset_statistics(dataset_folder: str) -> dict:
    """
    取得資料集統計資訊

    Args:
        dataset_folder: 資料集資料夾路徑

    Returns:
        dict: 統計資訊
    """
    folder = Path(dataset_folder)
    stats = {
        'total_images': 0,
        'total_labels': 0,
        'train': {},
        'val': {},
        'class_distribution': {}
    }

    for split in ['train', 'val']:
        img_dir = folder / 'images' / split
        label_dir = folder / 'labels' / split

        if img_dir.exists():
            images = list(img_dir.glob('*.*'))
            stats[split]['images'] = len(images)
            stats['total_images'] += len(images)

        if label_dir.exists():
            labels = list(label_dir.glob('*.txt'))
            stats[split]['labels'] = len(labels)
            stats['total_labels'] += len(labels)

            # 統計類別分布
            for label_file in labels:
                try:
                    with open(label_file, 'r') as f:
                        for line in f:
                            cls_id = int(line.split()[0])
                            stats['class_distribution'][cls_id] = \
                                stats['class_distribution'].get(cls_id, 0) + 1
                except Exception as e:
                    logger.warning(f"讀取標註失敗 {label_file}: {e}")

    return stats
