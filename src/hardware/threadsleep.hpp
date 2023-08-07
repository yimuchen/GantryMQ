/**
 * @file threadsleep.hpp
 * @author Yi-Mu Chen
 * @brief Inline functions to help sleep threads
 * @date 2023-08-03
 */
#ifndef GANTRYMQ_THREADSLEEP_HPP
#define GANTRYMQ_THREADSLEEP_HPP

#include <chrono>
#include <thread>

namespace hw
{

inline void
sleep_nanoseconds( const unsigned x )
{
  std::this_thread::sleep_for( std::chrono::nanoseconds( x ));
}


inline void
sleep_microseconds( const unsigned x )
{
  std::this_thread::sleep_for( std::chrono::nanoseconds( x * 1000 ));
}


inline void
sleep_milliseconds( const unsigned x )
{
  std::this_thread::sleep_for( std::chrono::nanoseconds( x * 1000 * 1000 ));
}


inline void
sleep_seconds( const unsigned x )
{
  std::this_thread::sleep_for( std::chrono::nanoseconds(
                                 x * 1000 * 1000 * 1000 ));
}

}

#endif
