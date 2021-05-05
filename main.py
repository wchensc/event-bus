# import time
#
# from event_bus import EventBus
#
# eb = EventBus()
#
# class x:
#     def __init__(self):
#         eb.add_event(self.a, "1")
#         eb.add_event(self.b, "1", thread=True)
#
#     def a(self, d=1):
#         print("start a")
#         time.sleep(2)
#         print("end a" + str(d))
#
#     def b(self, d=1):
#         print("start b")
#         time.sleep(2)
#         print("end b" + str(d))
#
# class x2:
#     def __init__(self):
#         eb.add_event(self.a, "1", thread=True)
#         eb.add_event(self.b, "1", thread=True)
#
#     def a(self, d=1):
#         print("start another a")
#         time.sleep(2)
#         print("end another a" + str(d))
#
#     def b(self, d=1):
#         print("start another b")
#         time.sleep(2)
#         print("end another b" + str(d))
#
# if __name__ == '__main__':
#     x1 = x()
#     x2 = x2()
#     eb.emit("1")