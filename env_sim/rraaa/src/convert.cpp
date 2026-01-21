#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"
#include "std_msgs/msg/multi_array_dimension.hpp"

#include <octomap/octomap.h>
#include <octomap_msgs/msg/octomap.hpp>
#include <octomap_msgs/conversions.h>

#include <vector>



/**
 * @class OctomapMsgConverter
 * @brief Receive the octomap msg and convert it into multidimensional array for 3D path planning.
 *
 * Detailed description of the class and its purpose.
 * 
 * The following are the resources that I used.
 * 
 * Since the octomap msg is working well with RVIZ, the following RVIZ plugin C++ source should be the useful.
 * LINE 481 <--- look at here!   https://github.com/OctoMap/octomap_rviz_plugins/blob/kinetic-devel/src/occupancy_grid_display.cpp
 * 
 * The above uses the following "converstions.h"
 * https://github.com/OctoMap/octomap_msgs/blob/melodic-devel/include/octomap_msgs/conversions.h
 * 
 * =====================
 * Some basic c++ facts:
 * =====================
 * 
 * (pointer_name)->(variable_name)
 * 
 * Operation: The -> operator in C or C++ gives the value held by variable_name to structure or union variable pointer_name.
 * Difference between Dot(.) and Arrow(->) operator:  
 *
 * The Dot(.) operator is used to normally access members of a structure or union.
 * The Arrow(->) operator exists to access the members of the structure or the unions using pointers.
 * 
 * 
 * ============================================
 * Look at the below for multi-dim pub with ROS
 * ============================================
 * https://answers.ros.org/question/234028/how-to-publish-a-2-dimensional-array-of-known-values/
 * 
 * 
 * 
 * 
 */


class OctomapMsgConverter {

  private:
    double* array; // Pointer to the array
    int m;         // M Columns
    int n;         // N Rows
    std::size_t size=0;  // Size of the vector to return
    bool recvd = false;

  public:

    void Callback(const octomap_msgs::msg::Octomap::SharedPtr msg){

      recvd = true;

      // Map information
      octomap::AbstractOcTree* tree = octomap_msgs::msgToMap(*msg);

      double minX, minY, minZ, maxX, maxY, maxZ; 
      tree->getMetricMin(minX, minY, minZ); //map covering space limits
      tree->getMetricMax(maxX, maxY, maxZ); //min, max, X, Y, Z
      double resolution = tree->getResolution(); //get resolution of octree

      // Tree for iterating nodes
      octomap::OcTree* te = dynamic_cast<octomap::OcTree*>(tree);

      // Dimensions of the 2D array
      m = 5;                ; // m coloums or width
      n = te->calcNumNodes(); // n rows or height

      // Declare a memory block of size m*n
      array = new double[m * n];

      int i = 0;
      for (octomap::OcTree::leaf_iterator it = te->begin_leafs(); it != te->end_leafs(); ++it){
        array[i * m + 0] = it.getX();
        array[i * m + 1] = it.getY();
        array[i * m + 2] = it.getZ();
        array[i * m + 3] = it->getValue();
        array[i * m + 4] = te->isNodeOccupied(*it);
        
        i++;
      }
      n = i; // Number of row after filling-in values.
      size = m*n; 

      delete tree;

    }

    std::vector<double> getVector(){
      
      if (recvd){
        std::vector<double> vec(size,0); // vector to return
        for (int i=0; i<size; i++){
          vec[i] = array[i];
        };
        delete[] array;

        recvd = false;

        return vec;
      }
      else{
        std::vector<double> vec(1,0); // vector to return
        return vec;

      };
      
    }



    int getHeight(){
      return n;
    }

    int getWidth(){
      return m;
    }

};



int main(int argc, char **argv)
{

  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("node_converter");

  OctomapMsgConverter converter;

  auto sub = node->create_subscription<octomap_msgs::msg::Octomap>("/octomap_full", 1000, std::bind(&OctomapMsgConverter::Callback, &converter, std::placeholders::_1));
  auto pub = node->create_publisher<std_msgs::msg::Float64MultiArray>("/octomap_conv_array", 1);
  rclcpp::Rate loop_rate(10);

  std_msgs::msg::Float64MultiArray dat;


  // fill out message:
  dat.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
  dat.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
  dat.layout.dim[0].label = "row";
  dat.layout.dim[1].label = "x,y,z,value";


  int count = 0;
  while (rclcpp::ok())
  {
    std::vector<double> vec = converter.getVector();
    if (vec.size()>1)
    {
      int H = converter.getHeight();
      int W = converter.getWidth();
      dat.layout.dim[0].size = H;
      dat.layout.dim[1].size = W;
      dat.layout.dim[0].stride = H*W;
      dat.layout.dim[1].stride = W;
      dat.layout.data_offset = 0;
      dat.data = vec;
    }
  

    pub->publish(dat);

    vec.clear();


    rclcpp::spin_some(node);

    loop_rate.sleep();
    ++count;
  };

  rclcpp::shutdown();
  return 0;
}