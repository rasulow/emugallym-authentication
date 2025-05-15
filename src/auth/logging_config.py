import os
import logging
import logging.handlers
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Создаем директорию для логов, если она не существует
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now().isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['funcName'] = record.funcName
        log_record['lineNo'] = record.lineno
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'ip'):
            log_record['ip'] = record.ip
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging(env='production'):
    # Основной логгер
    logger = logging.getLogger('paytoleg')
    logger.setLevel(logging.INFO)
    
    # Форматтер для JSON логов
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(module)s %(funcName)s %(lineNo)d %(message)s'
    )

    # Файловый обработчик с ротацией по размеру
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, 'paytoleg.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Отдельный обработчик для ошибок
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, 'error.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # В режиме разработки добавляем вывод в консоль
    if env == 'development':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Создаем и настраиваем логгер при импорте модуля
logger = setup_logging()