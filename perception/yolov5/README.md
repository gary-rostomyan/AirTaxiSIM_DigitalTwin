> This document is a temporary reference for the ROS 2 update. Its accuracy cannot be fully verified, as the updater performs the update on macOS. 

> Updater's Note: I have ensured that the ROS 2 YOLO node is functional. However, inter-process communication has not been fully tested.

Please use 

```shell
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
mv yolov8n.pt /colcon_ws/src/yolov5/models/
```

To download a YOLO model in your Docker workspace. Or the ROS 2 node cannot run.
