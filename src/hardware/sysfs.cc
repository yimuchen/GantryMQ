#include "sysfs.hpp"
#include "threadsleep.hpp"

#include <fmt/core.h>

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
 * @brief Class for opening a file with locking flag, to ensure the instance is
 * the only process on the system that is using the path.
 *
 * @details This class wraps common file descriptor interactions, and ensures
 * uniqueness of the instance if requested. The locking happens at construction
 * time, following the solution given [here][ref]. In the case that the file
 * descriptor cannot be opened or the lock instance cannot be generated, the
 * existing file descriptor will be closed and a exception will be raised.
 * Notice that the system lock will automatically be removed when the
 * corresponding file descriptor is closed (no `funlock` operation is needed).
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
      this->close_with_error( fmt::format( "Failed to lock path [{0:s}]",
                                           dev_path ));
    }
  }
}


/**
 * @brief Boolean flag of whether the file descriptor is currently valid.
 */
bool
fd_accessor::is_valid() const
{
  return this->_fd != -1;
}


/**
 * @brief If file descriptor is not valid, raise and exception.
 */
void
fd_accessor::check_valid() const
{
  if( !this->is_valid() ){
    raise_error( fmt::format(
                   "File descriptor not initialized, fd value: [{0:d}]",
                   this->_fd ) );
  }
}


/**
 * @brief Ensuring the file descriptor is closed (in case the file descriptor
 * can be opened but wasn't able to run additional configuration), then raise
 * and error message.
 */
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
 * @brief Writing to the file descriptor.
 *
 * The additional checks that we will run for this operation would be:
 * - Whether the file descriptor is valid.
 * - Whether the written message length matches the message length.
 *
 * If either check fails, raise an error. We will return the write length.
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


/**
 * @brief Writing to the file descriptor (using strings).
 */
int
fd_accessor::write( const std::string& message ) const
{
  return this->write( std::vector<uint8_t>( message.begin(), message.end() ) );
}


/**
 * @brief Direct call of write.
 *
 * Direct passthrough of the write operation with not error or format checking.
 * Error checking should be handled by the function caller, or be skipped if
 * rapid writes is required.
 */
int
fd_accessor::write_raw( const char* message, const int n ) const
{
  return ::write( this->_fd, message, n );
}


/**
 * @brief Reading from the file descriptor to a string.
 *
 * User can specific a length to read. If not provided, then we simply read
 * however much is available at the file descriptor. If the read length is
 * provided, then we also check the return string length for it to ensure that
 * the matches the expected string length.
 */
std::string
fd_accessor::read_str( const unsigned n ) const
{
  static constexpr uint16_t buf_size = 65535;

  this->check_valid();
  char      buffer[buf_size] = {};
  const int readlen          = ( n == 0 ) ? //
                               ::read( this->_fd, buffer, sizeof( buffer )-1 ) : //
                               ::read( this->_fd, buffer, n );

  if( ( n > 0 )  && ( readlen != (int)n ) ){
    raise_error( fmt::format(
                   "mismatch message length. Expected [{0:d}], got [{1:d}]", n,
                   readlen ));
  }
  return std::string( buffer, buffer+readlen );
}


/**
 * @brief Reading from the file descriptor, and cast string to uint8 array.
 */
std::vector<uint8_t>
fd_accessor::read_bytes( const unsigned n ) const
{
  const std::string read_str = this->read_str( n );
  return std::vector<uint8_t>( read_str.begin(), read_str.end() );
}


/**
 * @brief Suspending the thread until the path becomes accessible.
 */
void
fd_accessor::wait_fd_access( const std::string& path )
{
  while( access( path.c_str(), F_OK ) == -1 ){
    hw::sleep_milliseconds( 100 );
  }
}


/**
 * @brief Ensuring the file descriptor closes when our class goes out of scope.
 */
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
 * Logging is elevated to the python logging modules for easier filtering and
 * formatting at user level. The function used is modified from here:
 * https://kalebporter.medium.com/logging-extending-python-with-c-or-c-fa746466b602
 *
 * @param name The name of the sublogger to use.
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


void
hw::fd_accessor::printdebug( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 6, msg );
}


void
hw::fd_accessor::printinfo( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 20, msg );
}


void
hw::fd_accessor::printmsg( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 20, msg );
}


void
hw::fd_accessor::printwarn( const std::string& msg ) const
{
  logger_wrapped( this->_dev_name, 30, msg );
}


/**
 * @brief Standard method for raising an error.
 */
void
hw::fd_accessor::raise_error( const std::string& msg ) const
{
  throw std::runtime_error( msg );
}
