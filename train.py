import model as m
import data
import hydra
from omegaconf import DictConfig, OmegaConf
from pytorch_lightning.callbacks import ModelCheckpoint, LearningRateMonitor
from hydra import initialize, compose
from pytorch_lightning import seed_everything
from pytorch_lightning.loggers import WandbLogger
import os
from pytorch_lightning import Trainer
import argparse


@hydra.main(version_base=None, config_path="config/train", config_name="default")
def train(cfg: DictConfig):    
    Model = m.get_model(model_name=cfg.model.task)
    train_dataloader, test_dataloader = data.get_dataloader(dataset_name=cfg.data.name)
    
    # Initialize Wandb logger with a careful naming convention for the model
    wandb_logger = WandbLogger(
        project=cfg.trainer.logger_project,
        save_dir=cfg.trainer.logger_save_dir,
        name=cfg.trainer.logger_name,
        log_model=True
    )

    # Callbacks
    checkpoint_callback = ModelCheckpoint(
        monitor=cfg.trainer.monitor_metric,
        dirpath=cfg.trainer.checkpoint_dir,
        filename="m_B_{epoch:02d}-{val_acc:.2f}",
        save_top_k=cfg.trainer.save_top_k,
        mode="max",
    )
    lr_monitor = LearningRateMonitor(logging_interval="step")

    # Path for latest checkpoint
    latest_checkpoint = None
    if os.path.exists(cfg.trainer.checkpoint_dir):
        checkpoints = os.listdir(cfg.trainer.checkpoint_dir)
        if checkpoints:
            latest_checkpoint = max(
                [os.path.join(cfg.trainer.checkpoint_dir, ckpt) for ckpt in checkpoints],
                key=os.path.getctime
            )

    # Training model instance
    model = Model(
        cfg.model.name,
        steps_per_epoch=len(train_dataloader),
        num_classes=cfg.model.num_classes,
        lr=cfg.model.lr
    )

    # Trainer configuration
    trainer = Trainer(
        max_epochs=cfg.trainer.max_epochs,
        logger=wandb_logger,
        callbacks=[checkpoint_callback, lr_monitor],
        accelerator=cfg.trainer.accelerator,
        devices=cfg.trainer.devices
    )

    # Model training
    trainer.fit(model, train_dataloaders=train_dataloader, val_dataloaders=test_dataloader)


def main():
    # Seed for reproducibility
    seed_everything(42)
    
    args = parse_args()
    config_name = args.config_name
        
    # Initialize Hydra and compose the config
    with initialize(config_path="config/train", version_base=None):
        cfg = compose(config_name=config_name)
        train(cfg)  # Call `train` with the composed config


def parse_args():
    parser = argparse.ArgumentParser(description="Training script")
    parser.add_argument('--config_name', type=str, default="m_B_100", help='Name of the configuration')
    return parser.parse_args()

if __name__ == "__main__":
    main()
