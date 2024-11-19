cmake_minimum_required(VERSION 3.29)
project(Practice_3)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY /home/golimghost/Desktop/CProj/Practice_3/bin)
include_directories(.)

add_executable(pr3
        libs.h
        main.cpp
        structures.h
        structures.cpp
)
