#include "sysfs.hpp"
#include "threadsleep.hpp"

//
#include <fmt/printf.h>

// For /sys filesystem interactions
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

// For managing the output system using python.logging library
#include "Python.h"
#include <stdexcept>

namespace hw
{

/**
 * @brief Opening a file with a lock to ensure the program is the only process on
 * the system that is using the path.
 *
 * Mainly following the solution given [here][ref]. In the case that the file
 * descriptor cannot be opened or the lock instance cannot be generated, the
 * existing file descriptor will be closed and a exception will be raised. Notice
 * that the system lock will automatically be removed when the corresponding file
 * descriptor is closed.
 *
 * [ref]: https://stackoverflow.com/questions/1599459/optimal-lock-file-method
 */
fd_accessor::fd_accessor( const std::string& dev_name,
                          const std::string& dev_path,
                          const int          mode,
                          const bool         lock )
{
  this->_dev_name = dev_name;
  this->_dev_path = dev_path;
  this->_mode     = mode;
  this->_fd       = open( dev_path.c_str(), mode );
  if( this->_fd == -1 ){
    raise_error( fmt::format( "Failed to open path [{0:s}]", dev_path ) );
  }

  // The _lock will be non-zero if the processes cannot create the lock instance
  if( lock ){
    if( flock( this->_fd, LOCK_EX | LOCK_NB ) ){
      this->close_with_error(
        fmt::format( "Failed to lock path [{0:s}]", dev_path ));
    }
  }
}


bool
fd_accessor::is_valid() const
{
  return this->_fd != -1;
}


void
fd_accessor::check_valid() const
{
  if( !this->is_valid() ){
    raise_error( fmt::format(
                   "File descriptor not initialized, fd value: [{0:d}]",
                   this->_fd ) );
  }
}


void
fd_accessor::close_with_error( const std::string& message )
{
  if( this->is_valid() ){
    ::close( this->_fd );
    this->_fd = -1;
  }
  raise_error( message );
}


std::string
fd_accessor::intarray_to_string( const std::vector<uint8_t>& message )
{
  std::string ans = "0x";
  for( auto x : message ){
    ans += fmt::format( "{0:X}", x );
  }
  return ans;
}


/**
 * @brief Writing to the file descriptor position. Throws exception is error
 * occurs.
 *
 * @param fd
 * @return int
 */
int
fd_accessor::write( const std::vector<uint8_t>& message ) const
{
  this->check_valid();
  int n_written =  ::write( this->_fd, message.data(), message.size() );
  if( n_written != (int)message.size() ){
    raise_error( fmt::format(
                   "Error writing [{0:s}] to file descriptor [{1:s}].  Expected [{2:d}], got [{3:d}]",
                   fd_accessor::intarray_to_string( message ),
                   this->_dev_path,
                   message.size(),
                   n_written ));
  }
  return n_written;
}


int
fd_accessor::write( const std::string& message ) const
{
  return this->write( std::vector<uint8_t>( message.begin(), message.end()));
}


/**
 * @brief Direct call of write with not error or format checking.
 */
int
fd_accessor::write_raw( const char* message, const int n ) const
{
  return ::write( this->_fd, message, n );
}


std::vector<uint8_t>
fd_accessor::read_bytes( const unsigned n ) const
{
  const std::string read_str = this->read_str( n );
  return std::vector<uint8_t>( read_str.begin(), read_str.end() );
}


std::string
fd_accessor::read_str( const unsigned n ) const
{
  static constexpr uint16_t buf_size = 65535;

  char      buffer[buf_size] = {};
  const int readlen          = ( n == 0 ) ? //
                               ::read( this->_fd, buffer, sizeof( buffer )-1 ) : //
                               ::read( this->_fd, buffer, n );

  if( ( n > 0 )  && ( readlen != (int)n ) ){
    raise_error( fmt::format(
                   "mismatch message length. Expected [{0:d}], got [{1:d}]",
                   n,
                   readlen ));
  }
  return std::string( buffer, buffer+readlen );
}


void
fd_accessor::wait_fd_access( const std::string& path )
{
  while( access( path.c_str(), F_OK ) == -1 ){
    hw::sleep_milliseconds( 100 );
  }
}


fd_accessor::~fd_accessor()
{
  if( this->is_valid() ){
    close( this->_fd );
  }
}

}


// Static objects used for logging.
static PyObject* logging_lib = PyImport_ImportModuleNoBlock( "logging" );

/**
 * @brief Wrapping the python.logging modules call into a C function.
 *
 * Function modified from here: https://kalebporter.medium.com/logging-extending-python-with-c-or-c-fa746466b602
 *
 * @param name The name of the logger
 * @param level The info level
 * @param message The message string
 */
static void
logger_wrapped( const std::string& device,
                int                level,
                const std::string& message )
{
  PyObject* logging_name =
    Py_BuildValue( "s", fmt::format( "GantryMQ.{0:s}", device ).c_str()  );
  PyObject* logging_args = Py_BuildValue( "(is)", level, message.c_str() );
  PyObject* logging_obj  = PyObject_CallMethod( logging_lib,
                                                "getLogger",
                                                "O",
                                                logging_name );
  PyObject_CallMethod( logging_obj, "log", "O", logging_args );
  Py_DECREF( logging_name );
  Py_DECREF( logging_args );
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemented as a parallel to the update method.
 */
void
hw::fd_accessor::printdebug( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 6, msg );
}


/**
 * @brief
 *
 */
void
hw::fd_accessor::printinfo( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 20, msg );
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemented as a parallel to the update method.
 */
void
hw::fd_accessor::printmsg( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 20, msg );
}


/**
 * @brief Printing a message on screen with the standard yellow `[WARNING]`
 * string at the start of the line.
 */
void
hw::fd_accessor::printwarn( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 30, msg );
}


void
hw::fd_accessor::raise_error( const std::string& msg ) const
{
  throw std::runtime_error( msg );
}
