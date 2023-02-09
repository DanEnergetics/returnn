"""
Wrapper for RETURNN datasets.

We make use of TorchData data pipelines.
"""

from __future__ import annotations
from typing import Callable, Optional
import torch.utils.data
from returnn.datasets.basic import Dataset as ReturnnDataset


ResetCallbackT = Callable[[ReturnnDataset], None]


class IterableDatasetWrapper(torch.utils.data.IterDataPipe):
    """
    Converts a RETURNN dataset into a PyTorch IterableDataset.
    """

    def __init__(self, returnn_dataset: ReturnnDataset, *, reset_callback: Optional[ResetCallbackT] = None):
        """
        :param returnn_dataset: dataset to be wrapped
        :param reset_callback: callback function to be called when the dataset is reset, e.g. to init the epoch
        """
        self._dataset = returnn_dataset
        self._reset_callback = reset_callback

    def reset(self):
        """
        :return:
        """
        if self._reset_callback:
            self._reset_callback(self._dataset)

    def __iter__(self):
        """
        :return: generator providing data samples in the form of a dict data_key -> data
        :rtype: Iterable[dict[str, numpy.ndarray]]
        """
        data_keys = self._dataset.get_data_keys()

        seq_index = 0
        while self._dataset.is_less_than_num_seqs(seq_index):
            self._dataset.load_seqs(seq_index, seq_index + 1)
            data = {data_key: self._dataset.get_data(seq_index, data_key) for data_key in data_keys}
            yield data
            seq_index += 1

    def __getitem__(self, index):
        raise Exception(f"{self.__class__.__name__}.__getitem__ not supported")


class MapStyleDatasetPerEpochWrapper(torch.utils.data.MapDataPipe):
    """
    Converts a RETURNN dataset into a PyTorch map-style Dataset.
    """

    def __int__(self, returnn_dataset: ReturnnDataset, *, reset_callback: Optional[ResetCallbackT] = None):
        """
        :param returnn_dataset: dataset to be wrapped
        :param reset_callback: callback function to be called when the dataset is reset, e.g. to init the epoch
        """
        assert returnn_dataset.have_corpus_seq_idx() and returnn_dataset.have_get_corpus_seq()
        self._dataset = returnn_dataset
        self._reset_callback = reset_callback

    def reset(self):
        """
        :return:
        """
        if self._reset_callback:
            self._reset_callback(self._dataset)

    def __len__(self):
        """
        :return: number of data samples in the dataset
        :rtype: int
        """
        return self._dataset.num_seqs

    def __getitem__(self, index):
        """
        :param int index:
        :return: data sample in the form of a dict data_key -> data
        :rtype: dict[str, numpy.ndarray]
        """
        corpus_seq_idx = self._dataset.get_corpus_seq_idx(index)
        seq = self._dataset.get_corpus_seq(corpus_seq_idx)
        return seq.features


class MapStyleDatasetFullWrapper(torch.utils.data.MapDataPipe):
    """
    Converts a RETURNN dataset into a PyTorch map-style Dataset.
    """

    def __int__(self, returnn_dataset: ReturnnDataset, *, reset_callback: Optional[ResetCallbackT] = None):
        """
        :param returnn_dataset: dataset to be wrapped
        :param reset_callback:
        """
        assert returnn_dataset.have_get_corpus_seq()
        self._dataset = returnn_dataset
        self._reset_callback = reset_callback

    def reset(self):
        """
        :return:
        """
        if self._reset_callback:
            self._reset_callback(self._dataset)

    def __len__(self):
        """
        :return: number of data samples in the dataset
        :rtype: int
        """
        return self._dataset.get_total_num_seqs()

    def __getitem__(self, index):
        """
        :param int index:
        :return: data sample in the form of a dict data_key -> data
        :rtype: dict[str, numpy.ndarray]
        """
        seq = self._dataset.get_corpus_seq(index)
        return seq.features
