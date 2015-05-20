import logging

import socket

log = logging.getLogger(__name__)


class ArgumentError(Exception):
    """
    Raised when an argument passed to an API method is invalid for the given
    command type.
    """
    pass


class CommandError(Exception):
    """
    Raised when the Saleaa software returns an error condition.
    """
    pass


class InvalidResponse(Exception):
    """
    Raised when a response from the API is not invalid or not recognizeable.
    """
    pass


class API(object):
    """
    A wrapper for the Saleae Logic Socket Scripting Interface.
    """

    interface_version = '1.1.32'

    def __init__(self, host='127.0.0.1', port=10429):
        log.debug('Begin API connection to %s:%s', host, port)
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def command(self, *args, multiline=False):
        s = ','.join(str(arg) for arg in args) + '\0'
        log.debug('Send: %r', s)
        s = s.encode('ascii')
        self.sock.sendall(s)
        data = b''
        while True:
            chunk = self.sock.recv(1024)
            log.debug('Recv: %r', chunk)
            data += chunk
            if len(chunk) < 1024:
                break

        resp = data.decode('ascii')
        lines = resp.split('\n')
        status = lines.pop(-1)

        if status == 'NAK':
            raise CommandError('Command failed: %r', resp)

        if status != 'ACK':
            raise InvalidResponse('Invalid response: %r', resp)

        if lines:
            lines = [line.split(', ') for line in lines]
            if multiline:
                return lines
            else:
                assert len(lines) == 1, "expected 1 line, got more"
                return lines[0]

    def set_trigger(self, *channels):
        """
        This command lets you configure the trigger. The command must be sent
        with the same number of parameters as there are channels in the
        software. For use with Logic, 8 parameters must be present. Blank
        parameters are allowed.

        Parameter value options:
            - (blank)
            - high
            - low
            - negedge
            - posedge
        """
        channels = [ch or '' for ch in channels]
        for ii, ch in enumerate(channels):
            if ch not in ('', 'high', 'low', 'negedge', 'posedge'):
                raise ArgumentError('Invalid trigger mode: %r for channel %d'
                                    % (ch, ii))
        return self.command('set_trigger', *channels)

    def set_number_of_samples(self, samples):
        """
        This command changes the number of samples to capture. You must specify
        a value that the software recognizes. (Note: the only allowed values
        are those in the drop-down menu in the software.)
        """
        try:
            samples = int(samples)
        except ValueError:
            raise ArgumentError('Invalid sample count: %r' % samples)
        self.command('set_num_samples', samples)

    def set_sample_rate(self, digital_sample_rate, analog_sample_rate):
        """
        This command changes the sample rate in the software. You must specify
        a sample rate which is listed in the software. There is currently no
        helper function to get a list of sample rates. (Note: To get the
        available sample rates use get_all_sample_rates).
        """
        self.command('set_sample_rate',
                     digital_sample_rate, analog_sample_rate)

    def get_available_sample_rates(self):
        """
        This command returns all the available sample rate combinations for the
        current performance level and channel combination.
        """
        resp = self.command('get_all_sample_rates', multiline=True)
        return [(int(digital), int(analog)) for digital, analog in resp]

    def get_performance_option(self):
        """
        This command returns the currently selected performance options.
        """
        resp = self.command('get_performance_option')
        return int(resp[0])

    def set_performance_option(self, value):
        """
        This command returns the currently selected performance options. Valid
        performance options are: 20, 25, 33, 50, and 100. Note: This call will
        change the sample rate currently selected.
        """
        if value not in (20, 25, 33, 50, 100):
            raise ArgumentError('Invalid performance option: %r' % value)
        return self.command('set_performance_option', value)

    def get_capture_pretrigger_buffer_size(self):
        """
        This command gets the pretrigger buffer size of the capture.
        """
        resp = self.command('get_capture_pretrigger_buffer_size')
        return int(resp[0])

    def set_capture_pretrigger_buffer_size(self, value):
        """
        This command sets the pretrigger buffer size of the capture. Note:
        Currently, the pretrigger buffer size has to be one of the following
        values: 1000000, 10000000, 100000000, or 1000000000.
        """
        if value not in (1000000, 10000000, 100000000, 1000000000):
            raise ArgumentError('Invalid performance option: %r' % value)
        return self.command('set_capture_pretrigger_buffer_size', value)

    def get_connected_devices(self):
        """
        This command will return a list of the devices currently connected to
        the computer. The connected device will have the return parameter
        ACTIVE at the end of the line.
        """
        return self.command('get_connected_devices', multiline=True)

    def select_active_device(self, device_number):
        """
        This command will select the device set for active capture. It takes
        one additional parameter: the index of the desired device as returned
        by the get_connected_devices function.

        Note: Indices start at 1, not 0.
        """
        try:
            device_number = int(device_number)
        except ValueError:
            raise ArgumentError('Invalid device number: %r' % device_number)
        self.command('select_active_device', device_number)

    def get_active_channels(self):
        """
        This command will return a list of the active channels.
        """
        resp = self.command('get_active_channels')
        digital = []
        analog = []
        current = None
        for el in resp:
            if el == 'digital_channels':
                current = digital
            elif el == 'analog_channels':
                current = analog
            else:
                current.append(int(el))
        return {
            'digital': digital,
            'analog': analog,
        }

    def set_active_channels(self, digital_channels=(), analog_channels=()):
        """
        This command allows you to set the active channels. Note: This feature
        is only supported on Logic 16, Logic 8 (2nd gen), Logic Pro 8, and
        Logic Pro 16.
        """
        args = []
        args += ['digital_channels']
        args += digital_channels
        args += ['analog_channels']
        args += analog_channels
        self.command('set_active_channels', *args)

    def reset_active_channels(self):
        """
        This command will set all channels active for the device.
        """
        self.command('reset_active_channels')

    def capture(self):
        """
        This command starts a capture. It will return NAK if an error occurs.
        """
        self.command('capture')

    def capture_to_file(self, path):
        """
        This command starts a capture, and then auto-saves the results to the
        specified file. If an error occurs, the command will return NAK.

        Note: You must have permissions to the destination path, or the save
        operation will fail. By default, applications won’t be able to save to
        the root of the C drive on windows. To do this, the Logic software must
        be launched with administrator privileges.
        """
        self.command('capture_to_file', path)

    def get_inputs(self):
        """
        This command has been disabled temporarily.
        """
        raise NotImplementedError

    def is_processing_complete(self):
        """
        With the introduction of analog channels, processing data is no longer
        instant and may take some time after the capture. You cannot export or
        save data until processing is complete (The commands will NAK). This
        command returns a Boolean expressing whether or not the software is
        done processing data.
        """
        return self.command('is_processing_complete')

    def save_to_file(self, path):
        """
        This command saves the results of the current tab to a specified file.
        (Write permission required, see capture to file.)

        (Note: Data processing much be complete before this command is ran or
        it may NAK. See "Is Processing Complete" to check if processing is done
        before exporting data.)
        """
        self.command('save_to_file', path)

    def load_from_file(self, path):
        """
        This command loads the results of previous capture from a specific file.
        """
        self.command('load_from_file', path)

    def export_data(self, path):
        """
        This function exports the data from the current capture to a file.
        There are several options which are needed to specify how the data will
        be exported: (Note: the options are order-specific. The software will
        send a NAK if the options are out of order.)

        (Note: Data processing much be complete before this command is ran or
        it may NAK. See “Is Processing Complete” to check if processing is done
        before exporting data)

        TODO: Support additional options in this command.
        """
        self.command('export_data', path)

    def get_analyzers(self):
        """
        This function will return a list of analyzers currently attached to the
        capture, along with indexes so you can access them later.
        """
        resp = self.command('get_analyzers', multiline=True)
        return [(label, int(idx)) for label, idx in resp]

    def export_analyzers(self, index, path, pipe_result=False):
        """
        This command is used to export the analyzer results to a specified
        file. Pass in the index from the get_analyzers function, along with the
        path to save to. Add a third, optional parameter to have the results
        piped back through the TCP socket to you.
        """
        args = [index, path]
        if pipe_result:
            args.append('extra_parameter')
        resp = self.command('export_analyzers', *args, multiline=True)
        if pipe_result:
            return resp


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    api = API()
    api.capture()
    #print(api.get_connected_devices())
