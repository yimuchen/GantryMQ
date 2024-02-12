#ifndef GANTRYMY_SYSFS_HPP
#define GANTRYMQ_SYSFS_HPP

#include <cstdint>
#include <string>
#include <sys/file.h>
#include <vector>

/**
 * @brief Helper methods for /sys file system interactions
 */
namespace hw {

/**
 * @brief Simple wrapper for ensuring the file descriptor access lifetime
 */
class fd_accessor
{
public:
  enum MODE
  {
    READ_ONLY  = O_RDONLY,
    WRITE_ONLY = O_WRONLY,
    READ_WRITE = O_RDWR
  };

  // All public class, but use with care
  std::string _dev_name;
  std::string _dev_path;
  int         _fd;
  int         _mode;
  // Constructor, effectively the open method
  fd_accessor( const std::string& dev_name, const std::string& path, const int mode, const bool lock = true );

  // which checking of if the file descriptor is valid or not
  void check_valid() const;
  bool is_valid() const;
  void close_with_error( const std::string& );

  // The read and write method
  int                  write( const std::vector<uint8_t>& message ) const;
  int                  write( const std::string& message ) const;
  std::vector<uint8_t> read_bytes( const unsigned n = 0 ) const;
  std::string          read_str( const unsigned n = 0 ) const;

  int write_raw( const char* message, const int len ) const;
  // Destructor, effectively the close method
  ~fd_accessor();

  // Additional static helper method;
  static void                 wait_fd_access( const std::string& );
  static std::vector<uint8_t> string_to_intarray( const std::string& str );
  static std::string          intarray_to_string( const std::vector<uint8_t>& arr );

  // Messaging functions

  /**
   * @{
   * @brief logging informations at a certain level.
   */
  void printdebug( const std::string& x ) const;
  void printinfo( const std::string& x ) const;
  void printmsg( const std::string& x ) const;
  void printwarn( const std::string& x ) const;

  /** @} */

  void raise_error( const std::string& x ) const;
};

}

#endif
