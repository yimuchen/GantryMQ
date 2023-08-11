#include "sysfs.hpp"
#include "threadsleep.hpp"

#include <fcntl.h>
#include <fmt/core.h>
#include <linux/i2c-dev.h>
#include <stdint.h>
#include <sys/ioctl.h>


#include <pybind11/pybind11.h>

/**
 * @brief Specialized interactions with the ADS1115 ADC chip over an I2C device.
 *
 * @details Notice that all 4 channels will be forced to have identical
 * settings. While I2C devices must write operations to read data, since writes
 * are effectively instant, we use this chip effectively as a read-only device.
 */
class i2c_ads1115 : private hw::fd_accessor
{
public:
  // Default constructor and destructor
  i2c_ads1115( const uint8_t bus_id, const uint8_t dev_id );
  i2c_ads1115( const i2c_ads1115& )  = delete;
  i2c_ads1115( const i2c_ads1115&& ) = delete;
  ~i2c_ads1115();

  // ADC Range setting code
  static constexpr uint8_t ADS_RANGE_6V   = 0x0;
  static constexpr uint8_t ADS_RANGE_4V   = 0x1;
  static constexpr uint8_t ADS_RANGE_2V   = 0x2;
  static constexpr uint8_t ADS_RANGE_1V   = 0x3;
  static constexpr uint8_t ADS_RANGE_p5V  = 0x4;
  static constexpr uint8_t ADS_RANGE_p25V = 0x5;

  static constexpr uint8_t ADS_RATE_8SPS   = 0x0;
  static constexpr uint8_t ADS_RATE_16SPS  = 0x1;
  static constexpr uint8_t ADS_RATE_32SPS  = 0x2;
  static constexpr uint8_t ADS_RATE_64SPS  = 0x3;
  static constexpr uint8_t ADS_RATE_128SPS = 0x4;
  static constexpr uint8_t ADS_RATE_250SPS = 0x5;
  static constexpr uint8_t ADS_RATE_475SPS = 0x6;
  static constexpr uint8_t ADS_RATE_860SPS = 0x7;

  float read_mv( const uint8_t channel,
                 const uint8_t range,
                 const uint8_t rate = ADS_RATE_250SPS ) const;
};

/**
 * @brief Opening the file descriptor. Notice that because all devices on the
 * same I2C bus uses the same file descriptor, we will *not* lock the file
 * descriptor. But we will need to add an additional I2C device operations to
 * the file descriptor.
 */
i2c_ads1115::i2c_ads1115( const uint8_t bus_id,  const uint8_t dev_id ) : //
  hw::fd_accessor( fmt::format( "ads1115@{0:#x}:{1:#x}", bus_id, dev_id ),  //
                   fmt::format( "/dev/i2c-{0:d}", bus_id ), //
                   hw::fd_accessor::MODE::READ_WRITE, false )
{
  // connect to ADS1115 as i2c slave
  if( ioctl( _fd, I2C_SLAVE, dev_id ) == -1 ){
    this->close_with_error(
      fmt::format( "Error: Couldn't access i2c [{0:d}@{:d}]!",
                   _dev_name,
                   dev_id ));
  }
}


/**
 * @brief Returning the readout at a certain channel in units of mVs
 *
 * @details For each operation, you will still need to set the read range and
 * the the sampling rate. The parsing of the write operations to raw bits is
 * taken from this reference: http://www.bristolwatch.com/rpi/ads1115.html
 */
float
i2c_ads1115::read_mv( const uint8_t channel,
                      const uint8_t range,
                      const uint8_t rate ) const
{
  // byte 1 configuration:
  // Always  | MUX channel | PGA bits  | MODE (0 for continuous)
  // 1       | 1  x    x   | x   x   x | 0
  const uint8_t byte_1 = ( 0x3 << 6 ) //
                         | (( channel & 0x3 ) << 4 ) //
                         | ( ( range & 0x7 ) << 1 ) //
                         | 0x0;

  // Configuration byte 2
  // rate bits | COM BITS (Leave as default)
  // x x x     | 0 0 0 1 1
  const uint8_t byte_2 = (( rate & 0x7 ) << 5 ) //
                         | 0b00011;

  // Set device to write mode (leading 1), then write configurations
  this->write( std::vector<uint8_t>( {1, byte_1, byte_2} ) );
  hw::sleep_milliseconds( 50 );

  // Resetting device to read mode
  this->write( std::vector<uint8_t>( {0} ) );
  hw::sleep_milliseconds( 50 );

  // Reading raw adc values
  std::vector<uint8_t> val_bytes = this->read_bytes( 2 );
  int16_t              val_int   = val_bytes[0] << 8 | val_bytes[1];

  // Conversion factor based on requested range.
  const float conv = range == ADS_RANGE_6V  ? 6144.0 / 32678.0 : //
                     range == ADS_RANGE_4V  ? 4096.0 / 32678.0 : //
                     range == ADS_RANGE_2V  ? 2048.0 / 32678.0 : //
                     range == ADS_RANGE_1V  ? 1024.0 / 32678.0 : //
                     range == ADS_RANGE_p5V ? 512.0 / 32678.0  : //
                     256.0 / 32678.0;
  return float(val_int) * conv;
}


i2c_ads1115::~i2c_ads1115()
{}


PYBIND11_MODULE( i2c_ads1115, m )
{
  pybind11::class_<i2c_ads1115>( m, "i2c_ads1115" )
  .def( pybind11::init<const uint8_t, const uint8_t>() )

  // Read-only methods.
  .def( "read_mv",
        &i2c_ads1115::read_mv,
        "Returning the readout values in mV",
        pybind11::arg( "channel" ), //
        pybind11::arg( "range" ), //
        pybind11::arg( "rate" ) = i2c_ads1115::ADS_RATE_250SPS )

  // All static variables are read-only
  .def_readonly_static( "ADS_RANGE_6V",    &i2c_ads1115::ADS_RANGE_6V )
  .def_readonly_static( "ADS_RANGE_4V",    &i2c_ads1115::ADS_RANGE_4V )
  .def_readonly_static( "ADS_RANGE_2V",    &i2c_ads1115::ADS_RANGE_2V )
  .def_readonly_static( "ADS_RANGE_1V",    &i2c_ads1115::ADS_RANGE_1V )
  .def_readonly_static( "ADS_RANGE_p5V",   &i2c_ads1115::ADS_RANGE_p5V )
  .def_readonly_static( "ADS_RANGE_p25V",  &i2c_ads1115::ADS_RANGE_p25V )
  .def_readonly_static( "ADS_RATE_8SPS",   &i2c_ads1115::ADS_RATE_8SPS )
  .def_readonly_static( "ADS_RATE_16SPS",  &i2c_ads1115::ADS_RATE_16SPS )
  .def_readonly_static( "ADS_RATE_32SPS",  &i2c_ads1115::ADS_RATE_32SPS )
  .def_readonly_static( "ADS_RATE_64SPS",  &i2c_ads1115::ADS_RATE_64SPS )
  .def_readonly_static( "ADS_RATE_128SPS", &i2c_ads1115::ADS_RATE_128SPS )
  .def_readonly_static( "ADS_RATE_250SPS", &i2c_ads1115::ADS_RATE_250SPS )
  .def_readonly_static( "ADS_RATE_475SPS", &i2c_ads1115::ADS_RATE_475SPS )
  .def_readonly_static( "ADS_RATE_860SPS", &i2c_ads1115::ADS_RATE_860SPS )
  ;
}
