import torch
from .cifar100 import train_dataset, test_dataset
from .indl32 import combined_trainset, combined_testset
from ._base import *
from torch.utils.data import ConcatDataset, DataLoader, Dataset

# Custom dataset wrapper to replace binary labels (0, 1) from any binary dataset
# into new labels (10, 11), while keeping CIFAR10 (0-9) unchanged
class LabelModifier(Dataset):
    def __init__(self, dataset):
        self.dataset = dataset
    
    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, idx):
        # Retrieve data and label from the original dataset
        data, label = self.dataset[idx]
        
        # Ensure label is a tensor
        if isinstance(label, tuple):
            label = label[0]  # Handle any tuple by extracting the first element
        
        # Ensure both data and label are tensors
        data = torch.tensor(data) if not isinstance(data, torch.Tensor) else data
        label = torch.tensor(label) if not isinstance(label, torch.Tensor) else label
        
        # Replace 0 with 10 and 1 with 11 in the labels
        label = torch.where(label == 0, torch.tensor(100), label)
        label = torch.where(label == 1, torch.tensor(101), label)
        
        return data, label

# Apply the label modification **only** on the binary classification dataset

# Apply LabelModifier to the binary classification datasets
modified_combined_trainset = LabelModifier(combined_trainset)
modified_combined_testset = LabelModifier(combined_testset)

# Now combine CIFAR10 with the modified binary datasets
combined_trainset_final = ConcatDataset([modified_combined_trainset, train_dataset])
combined_testset_final = ConcatDataset([modified_combined_testset, test_dataset])

# Create DataLoader for combined training dataset
trainloader_combined = DataLoader(combined_trainset_final, batch_size=64, shuffle=True, num_workers=num_workers, pin_memory=True)

# Create DataLoader for combined testing dataset (with labels changed to 11 and 12)
testloader_combined = DataLoader(combined_testset_final, batch_size=64, shuffle=False, num_workers=num_workers, pin_memory=True)
