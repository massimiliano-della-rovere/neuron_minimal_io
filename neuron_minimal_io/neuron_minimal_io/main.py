"""
Minimal example showing how easy is to interact with the Neuron.

TL;DR: Read:
    1. the NeuronIO.io method and 
    2. the documentation at the following [B] URL.

Useful URLs:
  · [A] https://github.com/Dygmalab/Bazecor
  · [B] https://github.com/Dygmalab/Bazecor/blob/development/FOCUS_API.md
"""


from enum import IntEnum
from typing import Generator

# https://pypi.org/project/pyserial/
from serial import Serial
from serial.tools.list_ports import comports as list_serial_ports
from serial.tools.list_ports_common import ListPortInfo


CHARSET = "ascii"
END_OF_CONTENT = "."

UI_TO_NEURON = "<<"
UI_FROM_NEURON = ">>"
UI_COMMENT = "##"
UI_QUESTION = "??"
UI_INFO = "++"
UI_TEMPLATE = f"{UI_FROM_NEURON} {{content}}"


# this is ListPortInfo.port.vid [A]
DYGMA_VENDOR_ID_RAISE = 0x1209
DYGMA_VENDOR_ID_DEFY = 0x35EF
DYGMA_VENDOR_ID_RAISE2 = 0x35EF
# this is ListPortInfo.port.pid [A]
RAISE_ANSI_PRODUCT_ID = 0x2201
RAISE_ISO_PRODUCT_ID = 0x2201
DEFY_WIRED_PRODUCT_ID = 0x0010
DEFY_WIRELESS_PRODUCT_ID = 0x0012
RAISE2_ANSI_PRODUCT_ID = 0x0021
RAISE2_ISO_PRODUCT_ID = 0x0023
# this is (ListPortInfo.port.vid, ListPortInfo.port.pid) [A]
LIST_PORT_PID_VID_PAIRS = {
    (DYGMA_VENDOR_ID_RAISE, RAISE_ANSI_PRODUCT_ID),
    (DYGMA_VENDOR_ID_RAISE, RAISE_ISO_PRODUCT_ID),
    (DYGMA_VENDOR_ID_RAISE2, RAISE2_ANSI_PRODUCT_ID),
    (DYGMA_VENDOR_ID_RAISE2, RAISE2_ISO_PRODUCT_ID),
    (DYGMA_VENDOR_ID_DEFY, RAISE2_ANSI_PRODUCT_ID),
    (DYGMA_VENDOR_ID_DEFY, RAISE2_ISO_PRODUCT_ID),
}


class LedMode(IntEnum):  # [B]
    NORMAL = 0
    WAVE = 1
    RAINBOW = 2


class NeuronIO:  # just a namespace to keep things tidy, i.e. a different file
    __slots__ = []

    @staticmethod
    def ndeserialize(output_line: bytes) -> str:
        # each line returned by readline will be like "something\r\n"
        return output_line.decode(CHARSET).strip()

    @staticmethod
    def nserialize(command: str) -> bytes:
        return f"{command.strip()}\n".encode(CHARSET)

    @staticmethod
    def io(port: str, command: str) -> Generator[str, None, None]:
        with Serial(port) as serial:
            serial.write(NeuronIO.nserialize(command))  # [A]
            while (content := NeuronIO.ndeserialize(serial.readline())) != END_OF_CONTENT:  # [A]
                yield content


class NeuronChat:
    __slots__ = ["_port"]

    def __init__(self, port: str | None = None) -> None:
        if not port:
            ports = self.find_ports_with_dygma_products()
            if len(ports) == 1:
                port = ports[0].device
                print(f"Dygma keyboard detected on port {port}")
            else:
                raise RuntimeError("Could not find a connected Dygma keyboard")
        self._port: str = port

    @property
    def port(self) -> str:
        return self._port

    def __repr__(self) -> str:
        return f"{type(self)}(port={self._port})"

    @staticmethod
    def find_ports_with_dygma_products() -> tuple[ListPortInfo, ...]:
        return tuple(
            port_info
            for port_info in list_serial_ports()
            if (port_info.vid, port_info.pid) in LIST_PORT_PID_VID_PAIRS)

    def talk(self, command: str, verbose: bool = False) -> str:
        communication = NeuronIO.io(self._port, command)

        if verbose:
            output = [f"{UI_TO_NEURON} {command}: "]
            output.extend(
                UI_TEMPLATE.format(content=line)
                for line in communication)
        else:
            output = communication

        return "\n".join(output)


if __name__ == "__main__":
    nc = NeuronChat()

    print()

    print(f"{UI_COMMENT} Reading from the Neuron")
    print(nc.talk("hardware.version", True))  # [B]
    print(nc.talk("version", True))  # [B]

    print()

    print(f"{UI_COMMENT} Writing into the Neuron")
    for effect in (LedMode.RAINBOW, LedMode.WAVE, LedMode.NORMAL):
        print(f"{UI_INFO} {effect.name} Mode!")
        print(nc.talk(f"led.mode {effect}", True))  # [B]
        input(f"{UI_QUESTION} Press enter for next effect")

    print("Commands implemented in the firmware:")
    print(nc.talk("help", True))
