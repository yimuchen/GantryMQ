#include "sysfs.hpp"
#include "threadsleep.hpp"

#include <fmt/core.h>

// Pybind11
#include <pybind11/pybind11.h>

/**
 * @brief Wrapper for a working with the GPIO pins.
 *
 * @details GPIO must be defined via a BCM pin index, which is different from
 * the physical bin layout. You can find the pin mapping using the wiringPi's
 * `gpio readall` command.
 */
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
  static constexpr int READ       = O_RDONLY;
  static constexpr int WRITE      = O_WRONLY;
  static constexpr int READ_WRITE = O_RDWR;

  static std::string make_device_name( const uint8_t pin_idx, const int direction );
};

/**
 * @brief Opening the GPIO file descriptor for interacting with the GPIO pin of
 * interest.
 *
 * @details The user will need to specify the BCM pin index and the read/write
 * direction. As there are additional routines required to have the GPIO file
 * descriptors to be enabled in the system, those routines are define in the
 * make_device_name method. If this pre-routine fails, a exception will be
 * raised, and the primary file descriptor will never be initialized.
 */
gpio::gpio( const uint8_t pin_idx, const int direction )
  : //
  hw::fd_accessor( gpio::make_device_name( pin_idx, direction ),
                   fmt::format( "/sys/class/gpio/gpio{0:d}/value", pin_idx ), //
                   direction )
  , _pin_idx( pin_idx )
{
}

/**
 * @brief Static method of enabling a pin to be used.
 */
std::string
gpio::make_device_name( const uint8_t pin_idx, const int direction )
{
  // Enabling pin
  hw::fd_accessor( "GPIO_export", "/sys/class/gpio/export", hw::fd_accessor::MODE::WRITE_ONLY )
    .write( fmt::format( "{0:d}", pin_idx ) );
  hw::sleep_milliseconds( 100 );

  // Getting the direction path
  const std::string dir_path = fmt::format( "/sys/class/gpio/gpio{0:d}/direction", pin_idx );

  hw::fd_accessor::wait_fd_access( dir_path );
  hw::sleep_milliseconds( 100 );
  hw::fd_accessor( "GPIO_dir", dir_path, hw::fd_accessor::MODE::READ_WRITE )
    .write( ( direction == gpio::READ ) ? "in" : "out" );

  return fmt::format( "GPIO_{0:d}", pin_idx );
}

/**
 * @brief Additional routine needs to deallocate the the system resources of the
 * GPIO pin.
 */
gpio::~gpio()
{
  hw::fd_accessor( "GPIO_unexport", "/sys/class/gpio/unexport", hw::fd_accessor::MODE::WRITE_ONLY )
    .write( fmt::format( "{0:d}", this->_pin_idx ) );
}

/**
 * @brief Slow write operation to toggle the pin value. Run all typically write
 * checks. And raises exception checks fail.
 */
void
gpio::slow_write( const bool x ) const
{
  this->write( x ? "1" : "0" );
}

/**
 * @brief Slow read operation to check for current voltage value. Run all
 * typical read checks and raises exception if checks fail.
 */
bool
gpio::slow_read() const
{
  return this->read_str() == "1";
}

/**
 * @brief Generating N pulses with some time in between pulses. Only 1 validity
 * check will performed at the start of the function call.
 *
 * All pulses will have a high-time of 1 microsecond, and a w microsecond of
 * down time. The fastest pulse rate is about 100 microseconds.
 */
void
gpio::pulse( const unsigned n, const unsigned wait ) const
{
  check_valid();
  for( unsigned i = 0; i < n; ++i ) {
    this->write_raw( "1", 1 );
    hw::sleep_nanoseconds( 500 );
    this->write_raw( "0", 1 );
    hw::sleep_microseconds( wait );
  }
}

PYBIND11_MODULE( gpio, m )
{
  pybind11::class_<gpio>( m, "gpio" )
    .def( pybind11::init<const uint8_t, const int>() )

    // Command-like function calls
    .def( "slow_write", &gpio::slow_write )
    .def( "pulse", &gpio::pulse, pybind11::arg( "n" ), pybind11::arg( "wait" ) )

    // Read-only function calls.
    .def( "slow_read", &gpio::slow_read )

    .def_readonly_static( "READ", &gpio::READ )
    .def_readonly_static( "WRITE", &gpio::WRITE )
    .def_readonly_static( "READ_WRITE", &gpio::READ_WRITE );
}
