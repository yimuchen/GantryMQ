#include "threadsleep.hpp"

#include <fmt/core.h>
#include <gpiod.h> // New interface for working with GPIO
#include <stdio.h>
#include <string>
#include <unistd.h>

// Pybind11
#include <pybind11/pybind11.h>

/** @brief Wrapper for a working with the GPIO pins.
 *
 * @details Wee are using GPIO as simple digital toggles, so all GPIO devices
 * will be defined as output devices. Because now chips/lines number always be
 * created in pairs, each write request will attempt to reopen the devices in
 * question. The example code is taken from repository:
 * https://github.com/starnight/libgpiod-example
 */
class gpio
{
private:
  uint8_t            _pin_idx; // We only need to keep track of the line number
  struct gpiod_chip* _chip_ptr;
  struct gpiod_line* _line_ptr;

public:
  gpio( const uint8_t pin_idx );
  gpio( const gpio& )  = delete;
  gpio( const gpio&& ) = delete;
  ~gpio();

  // Simple High/low toggle for a GPIO line
  void write( const bool );
  // Fast pulsing result
  void pulse( const unsigned n, const unsigned wait );

private:
  const std::string _consume_str;

  void prepare();
  void release();
};

/**
 * @brief Logging the line number of interest
 */
gpio::gpio( const uint8_t pin_idx )
  : _pin_idx( pin_idx )
  , _chip_ptr( nullptr )
  , _line_ptr( nullptr )
  , _consume_str( fmt::format( "cons_gpio_{0:d}", _pin_idx ) )
{
}

gpio::~gpio()
{
  release();
}

/**
 *  @brief preparing the various devices for writing
 */
void
gpio::prepare()
{
  _chip_ptr = gpiod_chip_open_by_name( "gpiochip0" );
  if( !_chip_ptr ) {
    perror( "Open chip failed\n" );
    release();
  }

  _line_ptr = gpiod_chip_get_line( _chip_ptr, _pin_idx );
  if( !_line_ptr ) {
    perror( "Get line failed\n" );
    release();
  }

  const int ret = gpiod_line_request_output( _line_ptr, _consume_str.c_str(), 0 );
  if( ret < 0 ) {
    perror( "Request line as output failed\n" );
    release();
  }
}

/**
 * @brief Releasing the interface pointer
 **/
void
gpio::release()
{
  if( _line_ptr ) {
    gpiod_line_release( _line_ptr );
    _line_ptr = nullptr;
  }
  if( _chip_ptr ) {
    gpiod_chip_close( _chip_ptr );
    _chip_ptr = nullptr;
  }
}

/**
 * @brief Slow write operation to toggle the pin value. Run all typically write
 * checks. And raises exception checks fail.
 */
void
gpio::write( const bool x )
{
  prepare();
  if( _line_ptr ) {
    const int ret = gpiod_line_set_value( _line_ptr, x );
    if( ret < 0 ) {
      perror( "Set line output failed\n" );
    }
  }
  release();
}

/**
 * @brief Generating N pulses with some time in between pulses. Only 1 validity
 * check will performed at the start of the function call.
 *
 * All pulses will have a high-time of 1 microsecond, and a w microsecond of
 * down time. The fastest pulse rate is about 100 microseconds.
 */
void
gpio::pulse( const unsigned n, const unsigned wait )
{
  prepare();
  for( unsigned i = 0; i < n; ++i ) {
    const int ret1 = gpiod_line_set_value( _line_ptr, 1 );
    hw::sleep_nanoseconds( 5 );
    const int ret2 = gpiod_line_set_value( _line_ptr, 0 );
    hw::sleep_microseconds( wait );
  }
  release();
}

PYBIND11_MODULE( gpio, m )
{
  pybind11::class_<gpio>( m, "gpio" )
    .def( pybind11::init<const uint8_t>() )
    // Command-like function calls
    .def( "write", &gpio::write )
    .def( "pulse", &gpio::pulse, pybind11::arg( "n" ), pybind11::arg( "wait" ) );
}
