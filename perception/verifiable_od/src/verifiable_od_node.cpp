#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
// #include <autoware_msgs/DetectedObjectArray.h>
// #include <autoware_msgs/DetectedObject.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_types.h>
#include <vision_msgs/msg/detection3_d_array.hpp>
#include <vision_msgs/msg/detection3_d.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <visualization_msgs/msg/marker.hpp>

// #include "lib/depth_clustering/src/depth_clustering/api/api.h"
#include "api/api.h"
// #include "api.h"

#include <cmath>
#include <string>
#include <vector>


class airPerception : public rclcpp::Node {
public:

  void pointCloudCallback(const sensor_msgs::msg::PointCloud2::ConstSharedPtr& msg) {

    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::fromROSMsg(*msg, *cloud);

	  std::vector<Eigen::Vector3f> point_cloud_eigen;
    for (pcl::PointXYZ& point: cloud->points) {

      if (point.x*point.x + point.y*point.y + point.z*point.z > point_min_dis_threshold_) {
        Eigen::Vector3f point_eigen;

        point_eigen.x() = point.x;
        point_eigen.y() = point.y;
        point_eigen.z() = point.z;
        point_cloud_eigen.push_back(point_eigen);
      }
    }

    if (point_cloud_eigen.size() <= point_min_num_threshold_) {
      RCLCPP_INFO(this->get_logger(), "less than %u points", point_min_num_threshold_);
      return;
    }


    RCLCPP_INFO(this->get_logger(), "point cloud recieved, size: %d", (int)(point_cloud_eigen.size()) );

    std::string frame_name = std::to_string(frame_counter_);

    // RCLCPP_INFO(this->get_logger(), "processOneFrameForApollo");
    depth_clustering_->processOneFrameForApollo(frame_name, point_cloud_eigen);
    // RCLCPP_INFO(this->get_logger(), "getBoundingBox");
    auto bounding_box = depth_clustering_->getBoundingBox();


    auto& bounding_box_type = depth_clustering_->getParameter().bounding_box_type;
    // RCLCPP_INFO(this->get_logger(), "determine type");
    switch (bounding_box_type) {
	    case depth_clustering::BoundingBox::Type::Cube:
        // RCLCPP_INFO(this->get_logger(), "cube for frame %s", frame_name.c_str());
        break;
	    case depth_clustering::BoundingBox::Type::Polygon:
        // RCLCPP_INFO(this->get_logger(), "polygon for frame %s", frame_name.c_str());
        break;
      case depth_clustering::BoundingBox::Type::Flat:
        // RCLCPP_INFO(this->get_logger(), "flat for frame %s", frame_name.c_str());
        break;
      default:
        RCLCPP_INFO(this->get_logger(), "unknown bounding box type for frame %s", frame_name.c_str());
    }


    auto bounding_box_cubes = bounding_box->getFrameCube();

    vision_msgs::msg::Detection3DArray ros_bounding_boxes;
    visualization_msgs::msg::MarkerArray rviz_bounding_boxes;

    ros_bounding_boxes.header.stamp = this->now();
    ros_bounding_boxes.header.frame_id = "sensor";

    RCLCPP_INFO(this->get_logger(), "number of bounding boxes detected: %u", (unsigned)bounding_box_cubes->size());
    int i=0;
    for (const auto& cube: *bounding_box_cubes) {
      vision_msgs::msg::Detection3D ros_cube;
      Eigen::Vector3f position = std::get<0>(cube);
      Eigen::Vector3f size = std::get<1>(cube);
      float rotation = std::get<2>(cube);
      ros_cube.bbox.center.position.x = position.x();
      ros_cube.bbox.center.position.y = position.y();
      ros_cube.bbox.center.position.z = position.z();
      ros_cube.bbox.size.x = size.x();
      ros_cube.bbox.size.y = size.y();
      ros_cube.bbox.size.z = size.z();
      ros_cube.bbox.center.orientation.x = std::sin(rotation);
      ros_cube.bbox.center.orientation.y = std::cos(rotation);
      ros_cube.bbox.center.orientation.z = 0;
      ros_cube.bbox.center.orientation.w = 0;
      ros_bounding_boxes.detections.push_back(ros_cube);


      visualization_msgs::msg::Marker rviz_cube;
      rviz_cube.header.frame_id = "sensor";
      rviz_cube.header.stamp = this->now();
      rviz_cube.ns = "verifiable_od_detection";
      rviz_cube.action = visualization_msgs::msg::Marker::ADD;
      rviz_cube.id = i;
      rviz_cube.type = visualization_msgs::msg::Marker::CUBE;
      rviz_cube.scale = ros_cube.bbox.size;
      rviz_cube.pose = ros_cube.bbox.center;
      rviz_cube.color.r = (float)(i%3+1)/3;
      rviz_cube.color.g = (float)(i/3%3+1)/3;
      rviz_cube.color.b = (float)(i/9%3+1)/3;
      rviz_cube.color.a = 0.4;
      rviz_cube.lifetime.sec = 0;
      rviz_cube.lifetime.nanosec = 180000000;  // 0.18 seconds
      rviz_bounding_boxes.markers.push_back(rviz_cube);

      i++;
    }

    ros_bounding_box_pub_->publish(ros_bounding_boxes);
    rviz_bounding_box_pub_->publish(rviz_bounding_boxes);

    frame_counter_++;

  }

  airPerception() : Node("verifiable_od") {
    frame_counter_ = 0;

    cloud_topic_ = "/carla_node/lidar_point_cloud";
    sub_cloud_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        cloud_topic_, rclcpp::SensorDataQoS(), std::bind(&airPerception::pointCloudCallback, this, std::placeholders::_1));
    ros_bounding_box_pub_ = this->create_publisher<vision_msgs::msg::Detection3DArray>("depth_clustering_bounding_box", 10);
    rviz_bounding_box_pub_ = this->create_publisher<visualization_msgs::msg::MarkerArray>("verifiable_od_visulization", 10);

    point_min_dis_threshold_ = 0;
    point_min_num_threshold_ = 5;

    // TODO: change dir?
    depth_clustering_config_file_name_ = "/colcon_ws/install/verifiable_od/share/verifiable_od/cfg/depth_clustering_config_64.json";
    depth_clustering_log_directory_ = "/colcon_ws/log/verifiable_od";
    // need to change the directories above!!!

    depth_clustering_ = std::make_shared<depth_clustering::DepthClustering>();
    if (depth_clustering_) {
      RCLCPP_INFO(this->get_logger(), "Start to initialize Depth Clustering.");

      if (!depth_clustering_->initializeForApollo(depth_clustering_config_file_name_, depth_clustering_log_directory_))
        RCLCPP_INFO(this->get_logger(), "Failed to initialize Depth Clustering.");
      else
        RCLCPP_INFO(this->get_logger(), "Depth Clustering initialized.");
    }
    else
      RCLCPP_INFO(this->get_logger(), "Failed to create Depth Clustering.");


  }

private:
  unsigned frame_counter_;


  std::string cloud_topic_; //default input
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_cloud_;
  rclcpp::Publisher<vision_msgs::msg::Detection3DArray>::SharedPtr ros_bounding_box_pub_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr rviz_bounding_box_pub_;

  float point_min_dis_threshold_;
  unsigned point_min_num_threshold_;


  std::shared_ptr<depth_clustering::DepthClustering> depth_clustering_;
	std::string depth_clustering_config_file_name_;
  std::string depth_clustering_log_directory_;



};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);

  rclcpp::Logger logger = rclcpp::get_logger("verifiable_od");
  RCLCPP_INFO(logger, "verifiable_od module started");

  auto node = std::make_shared<airPerception>();

  rclcpp::spin(node);
  rclcpp::shutdown();

  return 0;
}
