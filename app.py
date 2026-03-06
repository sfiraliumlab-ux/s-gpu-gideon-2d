import numpy as np

class SKinematics:
    def __init__(self, genetic_code, vurf=1.618):
        # Превращаем строку 0/1 в массив векторов
        self.genome = [int(b) for b in genetic_code]
        self.vurf = vurf

    def get_servo_angles(self, time_step):
        """
        Расчет углов на основе генома и Вурфа.
        Каждая лапа (1-6) получает свою долю резонанса Бингла.
        """
        angles = {}
        for leg in range(6):
            # Извлекаем сегмент генома для каждой лапы
            segment = self.genome[leg*8 : (leg+1)*8]
            phase_offset = sum(segment) * (np.pi / 8)
            
            # Формула Басаргина: Угол = Sin(t * Vurf + Phase)
            # Это создает "холодное" движение без рывков
            base_angle = np.sin(time_step * self.vurf + phase_offset) * 45
            angles[f"leg_{leg}"] = {
                "coxa": base_angle,
                "femur": base_angle * 0.618, # Золотое сечение в рычагах
                "tibia": -base_angle * 0.382
            }
        return angles

# Пример инициализации из вашего кода:
code = "1010010010100000111101011100010010111010110110111000001111101010"
spider_core = SKinematics(code)
