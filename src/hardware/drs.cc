/**
 * @file drs.cc
 * @author Yi-Mu Chen
 * @brief A high level interface for the DRS4 serializer.
 *
 * @class DRSContainer
 * @ingroup hardware
 * @brief Handling interfacing between the DRS readout system.
 *
 * Here we provide a simpler interface to interface to initialize the DRS4
 * oscilloscope with the default settings required for SiPM data collection, as
 * well as abstraction for the typical actions of pulse-like waveform
 * acquisition and waveform summing, and status report. This is basically a
 * stripped down and specialized method found in the DRS4 [reference
 * program][ref] that serves as the main reference of this file.
 *
 * The collection will always be in single-shot mode, with no exposure the
 * methods required to this setting. Notice that the DRS4 will not have a
 * timeout for single shot mode once collection is requested, so the user will
 * be responsible for making sure that the appropriate trigger is provided.
 *
 * Though devices are automatically detected via the libusb library, as handled
 * by the upstream DRS software, for uniformity, we will still use the file
 * descriptor class, and have the underlying file descriptor point to a lock
 * file in the /tmp directory.
 *
 * [ref]: https://www.psi.ch/en/drs/software-download
 */
// Custom short hand directories
#include "sysfs.hpp"
#include "threadsleep.hpp"

// DRS library
#include "DRS.h"

// Standard C++ libraries
#include <fmt/core.h>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

// For python binding
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

class DRSContainer : private hw::fd_accessor
{
public:
  DRSContainer();
  DRSContainer( const DRSContainer& )  = delete;
  DRSContainer( const DRSContainer&& ) = delete;
  ~DRSContainer();

  void StartCollect();
  void ForceStop();

  // Setting commands
  void SetTrigger( const unsigned channel,
                   const double   level,
                   const unsigned direction,
                   const double   delay );
  void SetRate( const double frequency );
  void SetSamples( const unsigned );

  // Direct interfaces
  pybind11::array_t<float> GetWaveform( const unsigned channel );
  pybind11::array_t<float> GetTimeArray( const unsigned channel );

  // High level interfaces
  double WaveformSum( const unsigned channel,
                      const unsigned intstart = -1,
                      const unsigned intstop  = -1,
                      const unsigned pedstart = -1,
                      const unsigned pedstop  = -1 );
  void     RunCalib();
  int      TriggerChannel();
  int      TriggerDirection();
  double   TriggerDelay();
  double   TriggerLevel();
  double   GetRate();
  unsigned GetSamples();

  // Pausing functions
  void WaitReady();
  bool IsAvailable() const;
  bool IsReady();
  void CheckAvailable() const;

  // Debugging methods
  void DumpBuffer( const unsigned channel );

private:
  // Variables for handling the various handles.
  std::unique_ptr<DRS> drs;
  DRSBoard*            board;

  // Time samples
  double   triggerlevel;
  unsigned triggerchannel;
  int      triggerdirection;
  double   triggerdelay;
  unsigned samples;

  std::vector<float> GetWaveFormRaw( const unsigned channel );
  std::vector<float> GetTimeArrayRaw( const unsigned channel );

  static std::string make_lockfile();
};


/**
 * @brief Initializing the DRS4 container in single shot mode, and external
 * triggers.
 *
 * As the reference program is a bit verbose, here we reduce the input to what
 * is needed for out single-shot operation. We also include explicit settings
 * commented out to make sure future development doesn't open certain settings
 * that is already known to cause issues by accident.
 */
DRSContainer::DRSContainer() ://
  hw::fd_accessor( "DRS", make_lockfile(), hw::fd_accessor::MODE::READ_WRITE ),
  drs            ( nullptr ),
  board          ( nullptr )
{
  printdebug( "Setting up DRS devices..." );
  char str[256];
  drs = std::make_unique<DRS>();
  if( drs->GetError( str, sizeof( str ) ) ){
    drs = nullptr;
    raise_error( fmt::format( "Error created DRS instance: [{0:s}]", str ) );
  }
  if( !drs->GetNumberOfBoards() ){
    drs = nullptr;
    raise_error( "No DRS boards found" );
  }

  // Only getting the first board for now.
  board = drs->GetBoard( 0 );
  board->Init();
  printdebug( fmt::format(
                "Found DRS[{0:d}] board on USB, serial [{1:04d}], firmware [{2:5d}]\n",
                board->GetDRSType(),
                board->GetBoardSerialNumber(),
                board->GetFirmwareVersion() ));

  // Thread sleep to allow for settings to settle down
  hw::sleep_microseconds( 5 );

  // Running the various common settings required for the SiPM calibration
  // board->SetChannelConfig( 0, 8, 8 );// 1024 binning
  board->SetFrequency( 2.0, true );// Running at target 2GHz sample rate.
  // DO NOT ENABLE TRANSPARENT MODE!!!
  // board->SetTranspMode( 1 );
  // board->SetDominoMode( 0 );// Singe shot mode
  // board->SetReadoutMode( 1 );// Read most recent

  /* set input range to -0.5V ... +0.5V */
  board->SetInputRange( 0 );

  // DO NOT ENABLE INTERNAL CLOCK CALIBRATION!!
  // board->EnableTcal( 1 );
  // By default setting to use the external trigger
  SetTrigger( 4,// Channel external trigger
              0.05,// Trigger on 0.05 voltage
              1,// Rising edge
              0 );// 0 nanosecond delay by default.
  // Additional sleep for configuration to get through.
  hw::sleep_microseconds( 5 );

  printdebug( "Completed setting DRS Container" );
}


/**
 * @brief Waiting for the DRS4 to be ready for data transfer.
 *
 * This function will suspend the thread indefinitely until the DRS4 is ready
 * for data transfer operation. After the suspension, the data will always be
 * flushed to the main buffer (as this main program is only ever intended to be
 * done with the DRS4 running in single-shot mode).
 */
void
DRSContainer::WaitReady()
{
  CheckAvailable();
  while( board->IsBusy() ){
    hw::sleep_microseconds( 5 );
  } board->TransferWaves( 0, 8 );// Flush all waveforms into buffer.
}


/**
 * @brief Getting the time slice array for precision timing of a specific
 * channel.
 *
 * Notice that this only changes once a timing calibration is performed, so it
 * can be reused between calibration runs. However, it is found that the timing
 * variation from a regular interval deducted from the sample frequency is small
 * enough that this function is only included for the sake of debugging and
 * display. The timing returned is in units of nanoseconds.
 */
std::vector<float>
DRSContainer::GetTimeArrayRaw( const unsigned channel )
{
  static const unsigned len = 2048;
  float                 time_array[len];
  WaitReady();
  board->GetTime( 0, 2 * channel, board->GetTriggerCell( 0 ), time_array );
  return std::vector<float>( time_array, time_array+len );
}


/**
 * @brief Getting the time slice array for precision timing of a specific
 * channel. Casting to a numpy compatible array format.
 *
 * Here we also truncate the array according to the NSamples setting for the
 * instance.
 */
pybind11::array_t<float>
DRSContainer::GetTimeArray( const unsigned channel )
{
  return pybind11::array_t<float>( //
    GetSamples(),
    GetTimeArrayRaw( channel ).data() );
}


/**
 * @brief Returning the last collected waveform as an array of floats
 *
 * This is a lowest level interface with the DRS4 API, and so no conversion
 * will be returned here, the return vector will always be a fixed length long
 * (2048). Conversion should be handled by the other functions.
 *
 * Notice that this function will wait indefinitely for the board to finish
 * data collection. So the user is responsible for making sure that the
 * appropriate trigger signal is sent.
 */
std::vector<float>
DRSContainer::GetWaveFormRaw( const unsigned channel )
{
  static const unsigned len = 2048;
  float                 waveform[len];
  WaitReady();

  // Notice that channel index 0-1 both correspond to the the physical
  // channel 1 input, and so on.
  int status = board->GetWave( 0, channel * 2, waveform );
  if( status ){
    raise_error( "Error running DRSBoard::GetWave" );
  }
  return std::vector<float>( waveform, waveform+len );
}


/**
 * @brief Returning the last collected waveform as an array of floats, casting
 * to a numpy compatible array format.
 *
 * We also truncate the array to the n-sample setting.
 */
pybind11::array_t<float>
DRSContainer::GetWaveform( const unsigned channel )
{
  return pybind11::array_t<float>( //
    GetSamples(),
    GetWaveFormRaw( channel ).data() );
}


/**
 * @brief Returning the waveform of a given channel summed over the integration
 * window, with a pedestal subtraction if needed.
 *
 * The integration window and pedestal window is specified by sample indices,
 * so you will need to calculate the required window from the timing
 * information. The return will be single double for the waveform area in units
 * of mV x ns. Notice that timing information will *NOT* be used, as we simply
 * assuming perfect temporal spacing between the sampled values.
 *
 * In case you do not want to to perform pedestal subtraction, the starting the
 * stopping indices to the same value.
 */
double
DRSContainer::WaveformSum( const unsigned channel,
                           const unsigned _intstart,
                           const unsigned _intstop,
                           const unsigned _pedstart,
                           const unsigned _pedstop )
{
  const auto     waveform = GetWaveFormRaw( channel );
  const unsigned maxlen   = board->GetChannelDepth();
  double         pedvalue = 0;

  // Getting the pedestal value if required
  if( _pedstart != _pedstop ){
    const unsigned pedstart = std::max( unsigned(0), _pedstart );
    const unsigned pedstop  = std::min( maxlen, _pedstop );
    for( unsigned i = pedstart; i < pedstop; ++i ){
      pedvalue += waveform[i];
    }
    pedvalue /= (double)( pedstop-pedstart );
  }

  // Running the additional parsing.
  const unsigned intstart  = std::max( unsigned(0), _intstart );
  const unsigned intstop   = std::min( maxlen, _intstop );
  double         ans       = 0;
  const double   timeslice = 1.0 / GetRate();
  for( unsigned i = intstart; i < intstop; ++i ){
    ans += waveform[i];
  }
  ans -= pedvalue * ( intstop-intstart );
  ans *= -timeslice;// Negative to correct pulse direction
  return ans;
}


/**
 * @brief Setting the trigger
 *
 * For the channel, use 4 to set to external trigger. The level and direction
 * will only be used if the trigger channel is set to one of the readout
 * channels. Delay will always be in units of nanoseconds.
 */
void
DRSContainer::SetTrigger( const unsigned channel,
                          const double   level,
                          const unsigned direction,
                          const double   delay )
{
  CheckAvailable();
  board->EnableTrigger( 1, 0 );// Using hardware trigger
  board->SetTriggerSource( 1 << channel );
  triggerchannel = channel;

  // Certain trigger settings are only used for internal triggers.
  if( channel < 4 ){
    board->SetTriggerLevel( level );
    triggerlevel = level;
    board->SetTriggerPolarity( direction );
    triggerdirection = direction;
  }
  triggerdelay = delay;
  board->SetTriggerDelayNs( delay );

  // Sleeping to allow settings to settle.
  hw::sleep_microseconds( 500 );
}


/**
 * @brief Getting the trigger channel stored in object.
 */
int
DRSContainer::TriggerChannel()
{
  return triggerchannel;
}


/**
 * @brief Getting the trigger direction stored in object.
 */
int
DRSContainer::TriggerDirection()
{
  return triggerdirection;
}


/**
 * @brief Getting the trigger delay in the DRS instance.
 */
double
DRSContainer::TriggerDelay()
{
  return triggerdelay;
}


/**
 * @brief Getting the trigger level stored in object
 */
double
DRSContainer::TriggerLevel()
{
  return triggerlevel;
}


/**
 * @brief Setting the data sampling rate.
 *
 * Notice that this will not be the real sampling rate, the DRS will
 * automatically round to the closest available value.
 */
void
DRSContainer::SetRate( const double x )
{
  CheckAvailable();
  board->SetFrequency( x, true );
}


/**
 * @brief Getting the true sampling rate
 */
double
DRSContainer::GetRate()
{
  CheckAvailable();
  double ans;
  board->ReadFrequency( 0, &ans );
  return ans;
}


/**
 * @brief Getting the number of sample to store.
 */
unsigned
DRSContainer::GetSamples()
{
  return std::min( (unsigned)board->GetChannelDepth(), samples );
}


/**
 * @brief Setting the number of values to store by default
 */
void
DRSContainer::SetSamples( const unsigned x )
{
  samples = x;
}


/**
 * @brief Starting a single-shot collection request.
 */
void
DRSContainer::StartCollect()
{
  CheckAvailable();
  board->StartDomino();
}


/**
 * @brief Forcing the collection to stop.
 */
void
DRSContainer::ForceStop()
{
  CheckAvailable();
  board->SoftTrigger();
}


/**
 * @brief Checking that a DRS4 is available for operation. Throw exception if
 * not.
 */
void
DRSContainer::CheckAvailable() const
{
  if( !IsAvailable() ){
    raise_error( "DRS4 board is not available" );
  }
}


/**
 * @brief True/False flag for whether the DRS4 is available for operation.
 */
bool
DRSContainer::IsAvailable() const
{
  return drs != nullptr && board != nullptr;
}


/**
 * @brief Simple check for whether data collection has finished.
 */
bool
DRSContainer::IsReady()
{
  return !board->IsBusy();
}


/**
 * @brief Running the timing calibration.
 *
 * This C++ function will assume that the DRS is in a correct configuration to
 * be calibrated (all inputs disconnected).
 */
void
DRSContainer::RunCalib()
{
  // Dummy class for overloading the callback function
  class DummyCallback : public DRSCallback
  {
public:
    virtual void Progress( int ){} // Do nothing
  };
  CheckAvailable();

  // Running the time calibration and voltage calibration each time the DRS is
  // initialized.
  DummyCallback _d;
  board->SetFrequency( 2.0, true );
  board->CalibrateTiming( &_d );
  board->SetRefclk( 0 );
  board->CalibrateVolt( &_d );

  // After running, we will need to reset the board trigger configurations
  // By default setting to use the external trigger
  SetTrigger( TriggerChannel(),// Channel external trigger
              TriggerLevel(),// Trigger on 0.05 voltage
              TriggerDirection(),// Rising edge
              TriggerDelay() );// 0 nanosecond delay by default.
}


/**
 * @brief Simple method for creating the lock file in the /tmp directory.
 */
std::string
DRSContainer::make_lockfile()
{
  const std::string filename = "/tmp/drs.lock";

  // Checking if the lock file actually exists. Creating if not.
  std::fstream lock_fs;
  lock_fs.open( filename,
                std::fstream::in | std::fstream::out | std::fstream::app );

  if( !lock_fs ){
    lock_fs.open( filename,
                  std::fstream::in | std::fstream::out | std::fstream::trunc );
  }
  lock_fs.close();

  return filename;
}


DRSContainer::~DRSContainer()
{
  printdebug( "Deallocating the DRS controller" );
}


PYBIND11_MODULE( drs, m )
{
  pybind11::class_<DRSContainer>( m, "drs" )
  .def( pybind11::init<>() )

  // Operation functions
  .def( "force_stop",      &DRSContainer::ForceStop    )
  .def( "start_collect",   &DRSContainer::StartCollect )
  .def( "run_calibration", &DRSContainer::RunCalib     )
  .def( "set_trigger",     &DRSContainer::SetTrigger   )
  .def( "set_samples",     &DRSContainer::SetSamples   )
  .def( "set_rate",        &DRSContainer::SetRate      )

  // Data extraction function (operation-like)
  .def( "get_time_slice",  &DRSContainer::GetTimeArray )
  .def( "get_waveform",    &DRSContainer::GetWaveform  )
  .def( "get_waveformsum", &DRSContainer::WaveformSum  )

  // Getting configurations (read-only operations)
  .def( "get_trigger_channel",   &DRSContainer::TriggerChannel   )
  .def( "get_trigger_direction", &DRSContainer::TriggerDirection )
  .def( "get_trigger_level",     &DRSContainer::TriggerLevel     )
  .def( "get_trigger_delay",     &DRSContainer::TriggerDelay     )
  .def( "get_samples",           &DRSContainer::GetSamples       )
  .def( "get_rate",              &DRSContainer::GetRate          )
  .def( "is_available",          &DRSContainer::IsAvailable      )
  .def( "is_ready",              &DRSContainer::IsReady          )
  ;
}
