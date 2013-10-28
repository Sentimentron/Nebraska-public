cmake_minimum_required(VERSION 2.6)
PROJECT(LabelCluster CXX)

# Set up the system to copy into Nebraska/Build
SET(CMAKE_RUNTIME_OUTPUT_DIRECTORY ../../Build)

#
# CXXFLAGS=-g -std=c++0x -stdlib=libc++ -O3 -ffast-math 
# LDFLAGS=-lsqlite3 -stdlib=libc++ 

add_executable(Cluster main.cpp)

# Compiler flags
if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
	SET(PLATFORM_CXX_STANDARD "c++0x")
	SET(PLATFORM_CXX_FLAGS "-stdlib=libc++")
	# target_link_libraries(Cluster c++)
else ()
	SET(PLATFORM_CXX_STANDARD "c++11")
	SET(PLATFORM_CXX_FLAGS "")
endif ()

add_definitions(-Wall -W -g -O3 -ffast-math -std=${PLATFORM_CXX_STANDARD} ${PLATFORM_CXX_FLAGS})

target_link_libraries(Cluster sqlite3)
target_link_libraries(Cluster c++)

