cmake_minimum_required(VERSION 3.8)
project(SiPMControl CXX)

## Compiler settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_compile_options("-g")
add_compile_options("-O3")
add_compile_options("-Wall")
add_compile_options("-Wno-undef")

# General output settings
set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/modules )
set(INCLUDE)

## Finding common required binary
find_package(PythonLibs    3 REQUIRED)
find_package(PythonInterp  3 REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(OpenCV          REQUIRED)
find_package(fmt             REQUIRED)
find_package(Boost COMPONENTS serialization)


# The Picoscope library, this assumes that the interface has been added to the
# external directory
if( EXISTS "external/picoscope" )
  message("External package for picoscope found! "
          "Making the picoscope readout interface")
  set(PICOSCOPE_INCDIR  "external/picoscope/include/")
  set(PICOSCOPE_LIBDIR  "external/picoscope/lib/")
  set(PICOSCOPE_LIB     "ps5000")
endif()

# The python.logging passthorugh as a separate library
add_library(hwlogger SHARED src/hardware/logger.cc)
target_include_directories(hwlogger PRIVATE ${PYTHON_INCLUDE_DIRS})
target_link_libraries(hwlogger PRIVATE ${PYTHON_LIBRARIES})

## Libraries are supposed to be python modules
function(make_hardware_library libname)
  pybind11_add_module(${libname} SHARED ${ARGN})
  target_link_libraries(${libname} PRIVATE fmt::fmt hwlogger)
endfunction()

# Making the various interface classes
if( DRS_DEFINES )
  make_control_library(drs src/drs.cc)
  add_drs_requirements(drs)
  add_drs_requirements(c_drs)
  target_link_libraries(c_drs PRIVATE c_logger fmt::fmt)
endif()


make_hardware_library(gcoder src/hardware/gcoder.cc )


## The DRS4 library, this assumes that the stuff have been added to the
if( EXISTS "external/drs" )
  message("External package DRS found! Making the DRS readout interface")

  # Must use the wxwidgets
  find_package(wxWidgets COMPONENTS core base)
  if(NOT wxWidgets_FOUND)
    message(FATAL_ERROR "DRS must require wx widgets to be installed")
  endif()
  include(${wxWidgets_USE_FILE})

  # Selecting the minimum required files for running the interface defined in
  # the DRS.hpp interface.
  set(DRS_DEFINES OS_LINUX HAVE_LIBUSB HAVE_LIBUSB10 USE_DRS_MUTEX)
  set(DRS_SRC "src/hardware/drs.cc"
              "external/drs/src/DRS.cpp"
              "external/drs/src/averager.cpp"
              "external/drs/src/mxml.c"
              "external/drs/src/strlcpy.c"
              "external/drs/src/musbstd.c")
  # Since there is are stray c files, force to be compiled as C++
  set_source_files_properties(${DRS_SRC} PROPERTIES LANGUAGE CXX)
  make_hardware_library(drs ${DRS_SRC})
  target_include_directories(drs PRIVATE "external/drs/include/")
  target_compile_definitions(drs PRIVATE ${DRS_DEFINES})
  target_link_libraries(drs PRIVATE usb ${wxWidgets_LIBRARIES})
endif()


# make_hardware_library(gpio src/hardware/gpio.cc)
#
# make_hardware_library(visual src/hardware/visual.cc)
# target_link_libraries( c_visual PRIVATE  c_logger
#                                          ${OpenCV_LIBS}
#                                          Threads::Threads
#                                          pybind11::pybind11
#                                          pybind11::python_link_helper
#                                          fmt::fmt)
# #message( "TESTING" ${PYTHON#_INCLUDE_DIRS} )
# target_include_directories(c_visual PRIVATE ${OpenCV_INCLUDE_DIRS}
#                                             ${PYTHON_INCLUDE_DIRS} )
# target_include_directories(visual PRIVATE ${OpenCV_INCLUDE_DIRS} )
#