#include "sysfs.hpp"
#include "threadsleep.hpp"

#include <fcntl.h>
#include <fmt/core.h>
#include <linux/i2c-dev.h>
#include <stdint.h>
#include <sys/ioctl.h>

#include <pybind11/pybind11.h>

/**
 * @brief Specialized interactions with the MCP4725DAC chip over an I2C.
 *
 * @details Write only device with only 1 channel
 */
class i2c_mcp4725 : private hw::fd_accessor
{
public:
  // Default constructor and destructor
  i2c_mcp4725( const uint8_t bus_id, const uint8_t dev_id );
  i2c_mcp4725( const i2c_mcp4725& )  = delete;
  i2c_mcp4725( const i2c_mcp4725&& ) = delete;
  ~i2c_mcp4725();


  void set_int( const uint16_t val ) const;
  int  read_int() const;
};

/**
 * @brief Opening the file descriptor. Notice that because all devices on the
 * same I2C bus uses the same file descriptor, we will *not* lock the file
 * descriptor. But we will need to add an additional I2C device operations to
 * the file descriptor.
 */
i2c_mcp4725::i2c_mcp4725( const uint8_t bus_id, const uint8_t dev_id ) :                                                                           //
  hw::fd_accessor( fmt::format( "ads1115@{0:#x}:{1:#x}", bus_id, dev_id ),  //
                   fmt::format( "/dev/i2c-{0:d}", bus_id ),                 //
                   hw::fd_accessor::MODE::READ_WRITE, false )
{
  // connect to ADS1115 as i2c slave
  if( ioctl( _fd, I2C_SLAVE, dev_id ) == -1 ){
    this->close_with_error( fmt::format(
                              "Error: Couldn't access i2c [{0:d}@{:d}]!",
                              _dev_name, dev_id ));
  }
}


/**
 * @brief Setting via 12 bit integer value
 *
 * Setting by value will require reading the driving voltage, so only supporting
 * in on C++ side for now.
 */
void
i2c_mcp4725::set_int( const uint16_t value ) const
{
  const uint8_t cmd    = 0b01000000; // Write to DAC only (no EEPROM)
  const uint8_t byte_0 =  cmd;
  const uint8_t byte_1 = (( value & 0b111111110000 ) >> 4 );
  const uint8_t byte_2 = (( value & 0b000000001111 ) << 4 ); // Must be shifted by 4
  //const uint8_t byte_3 = 0; // Must be shifted by 4

  this->write( std::vector<uint8_t>( {byte_0, byte_1, byte_2} ) );
}


int
i2c_mcp4725::read_int() const
{
  const std::vector<uint8_t> v =  this->read_bytes( 3 );
  return ( int(v[1]) << 4 ) |  ( int(v[2]) >> 4 );
}


i2c_mcp4725::~i2c_mcp4725() {}

PYBIND11_MODULE( i2c_mcp4725, m ) {
  pybind11::class_<i2c_mcp4725>( m, "i2c_mcp4725" )
  .def( pybind11::init<const uint8_t, const uint8_t>())
  .def( "set_int",
        &i2c_mcp4725::set_int,
        "Setting the output voltage (int)",
        pybind11::arg( "value" ))
  .def( "read_int", &i2c_mcp4725::read_int, "readout int int value" )
  ;
}
