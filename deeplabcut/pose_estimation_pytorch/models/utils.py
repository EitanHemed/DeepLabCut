import numpy as np
import torch


def generate_heatmaps(cfg: dict,
                      coords: np.array,
                      heatmap_size: tuple = (64, 64),
                      heatmap_type: str = 'gaussian'):
    if heatmap_type == 'gaussian':
        scmap, weights, locref_map, locref_mask = gaussian_scmap(cfg,
                                                                 coords,
                                                                 heatmap_size)
    else:
        raise ValueError('Only gaussian heatmap is supported!')
    scmap = torch.FloatTensor(scmap)
    if weights:
        weights = torch.FloatTensor(weights)
    locref_map = torch.FloatTensor(locref_map)
    locref_mask = torch.FloatTensor(locref_mask)
    
    return scmap, weights, locref_map, locref_mask


# Copy from dlc
def gaussian_scmap(cfg, coords, heatmap_size):
    """

    Parameters
    ----------
    cfg: dlc config
    Standart dlc config in the dlc project folder
    joint_id:
    coords: list/np.array of coordinates
    data_item
    heatmap_size
    scale

    Returns
    -------

    """
    locref_scale = 1.0 / cfg["locref_stdev"]
    num_joints = cfg["num_joints"]
    # stride = cfg['stride'] # Apparently, there is no stride in the cfg
    stride = 8  # TODO just test
    scmap = np.zeros((
        heatmap_size[0],
        heatmap_size[1], num_joints), dtype=np.float32)

    locref_map = np.zeros((
        heatmap_size[0],
        heatmap_size[1], num_joints * 2), dtype=np.float32)
    locref_mask = np.zeros_like(locref_map)

    width = heatmap_size[1]
    height = heatmap_size[0]
    dist_thresh = float((width + height) / 6)
    dist_thresh_sq = dist_thresh ** 2

    std = dist_thresh / 4
    grid = np.mgrid[:height, :width].transpose((1, 2, 0))
    grid = grid * stride + stride / 2
    for i, coord in enumerate(coords):
        coord = np.array(coord)[::-1]
        dist = np.linalg.norm(grid - coord, axis=2) ** 2
        scmap_j = np.exp(-dist / (2 * std ** 2))
        scmap[:, :, i] = scmap_j
        locref_mask[dist <= dist_thresh_sq, i * 2 + 0] = 1
        locref_mask[dist <= dist_thresh_sq, i * 2 + 1] = 1
        dx = coord[1] - grid.copy()[:, :, 1]
        dy = coord[0] - grid.copy()[:, :, 0]
        locref_map[:, :, i * 2 + 0] = dx * locref_scale
        locref_map[:, :, i * 2 + 1] = dy * locref_scale
    weights = None
    # weights = self.compute_scmap_weights(scmap.shape, joint_id, data_item)
    return scmap, weights, locref_map, locref_mask


# TODO: check this function and rewrite above
def _generate_heatmaps(keypoints,
                       heatmap_size,
                       image_size=(256, 256),
                       sigma=5):
    """
    TODO: MAKE FASTER
    Parameters
    ----------
    keypoints
    heatmap_size
    image_size
    sigma

    Returns
    -------

    """
    target = torch.zeros((keypoints.shape[0],
                          heatmap_size[1],
                          heatmap_size[0]), dtype=torch.float32)
    scale_x = heatmap_size[0] / image_size[0]
    scale_y = heatmap_size[1] / image_size[1]
    for joint_id in range(keypoints.shape[0]):
        mu_x = keypoints[joint_id, 0] * scale_x
        mu_y = keypoints[joint_id, 1] * scale_y
        if mu_x == -1:
            continue

        x = torch.arange(0, heatmap_size[0], 1, dtype=torch.float32)
        y = torch.arange(0, heatmap_size[1], 1, dtype=torch.float32)
        y = y[:, None]

        if mu_x > 0:
            target[joint_id] = torch.exp(- ((x - mu_x) ** 2 + (y - mu_y) ** 2) / (2 * sigma ** 2))

    return target


def sigmoid(tx: np.ndarray):

    exp_x = np.exp(tx)
    return exp_x / (1 + exp_x)