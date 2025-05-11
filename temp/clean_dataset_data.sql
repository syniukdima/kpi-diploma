-- Видалення даних з таблиці raw_metrics
DELETE FROM raw_metrics 
WHERE service_name LIKE 'dataset_service_%';

-- Видалення даних з таблиці processed_metrics
DELETE FROM processed_metrics 
WHERE service_name LIKE 'dataset_service_%';

-- Підтвердження видалення
SELECT 'Дані видалено успішно' AS result; 