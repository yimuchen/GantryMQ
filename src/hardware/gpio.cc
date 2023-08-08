#include "sysfs.hpp"
#include "threadsleep.hpp"

#include <fmt/core.h>

// Pybind11
#include <pybind11/pybind11.h>

class gpio : private hw::fd_accessor
{
private:
  uint8_t _pin_idx;

public:
  gpio( const uint8_t pin_idx, const int direction );
  gpio( const gpio& )  = delete;
  gpio( const gpio&& ) = delete;
  ~gpio();

  // Overloading the simple interactions
  void slow_write( const bool ) const;
  bool slow_read() const;

  void pulse( const unsigned n, const unsigned wait ) const;

  // Static flags for helping with settings
  static constexpr int READ  = O_RDONLY;
  static constexpr int WRITE = O_WRONLY;

  static std::string make_device_name( const uint8_t pin_idx,
                                       const int     direction );
};


gpio::gpio( const uint8_t pin_idx, const int direction ) :      //
  // Getting the required descriptor files initialized befor actually opening
  // the primary file descriptor.
  hw::fd_accessor( gpio::make_device_name( pin_idx, direction ),
                   fmt::format( "/sys/class/gpio/gpio{0:d}/value", pin_idx ),  //
                   direction ),
  _pin_idx       ( pin_idx )
{}


gpio::~gpio()
{
  hw::fd_accessor( "GPIO_unexport",
                   "/sys/class/gpio/unexport",
                   hw::fd_accessor::MODE::WRITE_ONLY )
  .write( fmt::format( "{0:d}", this->_pin_idx ));
}


std::string
gpio::make_device_name( const uint8_t pin_idx, const int direction )
{
  // Enabling pin
  hw::fd_accessor( "GPIO_export", "/sys/class/gpio/export", O_WRONLY )
  .write( fmt::format( "{0:d}", pin_idx ) );
  hw::sleep_milliseconds( 1 );

  // Getting the direction path
  const std::string dir_path = fmt::format(
    "/sys/class/gpio/gpio{0:d}/direction",
    pin_idx );

  hw::fd_accessor::wait_fd_access( dir_path );
  hw::sleep_milliseconds( 1 );
  hw::fd_accessor( "GPIO_dir", dir_path, O_RDWR )
  .write( ( direction == gpio::READ ) ? "in" : "out" );

  return fmt::format( "GPIO_{0:d}", pin_idx );
}


void
gpio::slow_write( const bool x ) const
{
  this->write( x ? "1" : "0" );
}


bool
gpio::slow_read() const
{
  return this->read_str() == "1";
}


/**
 * @brief Generating N pulses with some time in between pulses.
 *
 * All pulses will have a high-time of 1 microsecond, and a w microsecond of
 * down time. The fastest pulse rate is about 100 microseconds.
 */
void
gpio::pulse( const unsigned n, const unsigned wait ) const
{
  check_valid();
  for( unsigned i = 0; i < n; ++i ){
    this->write_raw( "1", 1 );
    hw::sleep_nanoseconds( 500 );
    this->write_raw( "0", 1 );
    hw::sleep_microseconds( wait );
  }
}


PYBIND11_MODULE( gpio, m )
{
  pybind11::class_<gpio>( m, "gpio" )

  // Explicitly hiding the constructor instance, using just the instance method
  // for getting access to the singleton class.
  .def( pybind11::init<const uint8_t, const int>() )

  // Hiding functions from python
  .def( "slow_write",      &gpio::slow_write     )
  .def( "slow_read",       &gpio::slow_read      )
  .def( "pulse",           &gpio::pulse          )

  .def_readonly_static( "READ",  &gpio::READ )
  .def_readonly_static( "WRITE", &gpio::WRITE )
  ;
}
