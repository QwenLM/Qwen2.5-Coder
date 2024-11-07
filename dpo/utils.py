import os
import logging
import transformers
from transformers.trainer_callback import TrainerControl, TrainerState
from transformers.training_args import TrainingArguments


def init_logger(fpath='', local_rank=0):
    if transformers.trainer_utils.is_main_process(local_rank):
        if fpath:
            if os.path.dirname(fpath):
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
            file_handler = logging.FileHandler(fpath, mode='a')  # to file
            transformers.logging.add_handler(file_handler)
        transformers.logging.set_verbosity_info()
    else:
        transformers.logging.set_verbosity_error()  # reduce
    transformers.logging.enable_explicit_format()
    return transformers.logging.get_logger()


def add_custom_callback(trainer, logger):
    if 'PrinterCallback' in trainer.callback_handler.callback_list:
        trainer.pop_callback(transformers.PrinterCallback)
    trainer.add_callback(LogCallback(logger))
    logger.info('Add custom LogCallback')
    logger.info(f"trainer's callbacks: {trainer.callback_handler.callback_list}")


class LogCallback(transformers.TrainerCallback):
    """
    A bare :class:`~transformers.TrainerCallback` that just prints with logger.
    """
    def __init__(self, logger, exclude=('total_flos', 'epoch')):
        self.logger = logger
        self.exclude = exclude

    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.is_world_process_zero:
            self.logger.info(''.join([
                f"[global_steps={state.global_step}]",
                f"[epochs={logs['epoch']}]",
                ','.join(f'{k}={v}' for k, v in logs.items()
                         if k not in self.exclude)
            ]))


class DatasetUpdateCallback(transformers.TrainerCallback):
    def __init__(self, trainer):
        self.trainer = trainer

    def on_epoch_begin(self, args, state, control, **kwargs):
        sampler = self.trainer.callback_handler.train_dataloader.sampler
        self.trainer.train_dataset.update(sampler.epoch)


class SaveDiskCallback(transformers.TrainerCallback):
    def on_save(self, args, state, control, **kwargs):
        if args.local_rank != 0:
            return

        for ckpt in os.listdir(args.output_dir):
            # remove out-of-date deepspeed checkpoints
            if ckpt.startswith('checkpoint-') and not ckpt.endswith(f'-{state.global_step}'):
                for pattern in ['global_step*', '*.pth']:
                    os.system("rm -rf " + os.path.join(args.output_dir, ckpt, pattern))

    def on_train_end(self, args, state, control, **kwargs):
        if state.is_local_process_zero:
            for pattern in ['global_step*', '*.pth']:
                os.system("rm -rf " + os.path.join(args.output_dir, "checkpoint-*", pattern))
