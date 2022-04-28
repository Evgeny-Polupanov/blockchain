from vehicle import Vehicle


class Bus(Vehicle):
    def __init__(self):
        super().__init__(starting_top_speed=100)
        self.passengers = []

    def add_group(self, passengers):
        self.passengers.extend(passengers)
