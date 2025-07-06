library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity ascii_output_gen is
    Port (
        clk          : in  std_logic;
        trigger_in   : in  std_logic;
        period_value : in  std_logic_vector(31 downto 0);
        mode_select  : in  std_logic_vector(1 downto 0); -- NEW: mode select input
        value        : out std_logic_vector(7 downto 0);
        data_valid   : out std_logic
    );
end ascii_output_gen;

architecture Behavioral of ascii_output_gen is

    -- Message: "FPGAPS: Hello World! 12345!"
    type ascii_array_t is array(0 to 25) of std_logic_vector(7 downto 0);
    constant ascii_message : ascii_array_t := (
        x"46", x"50", x"47", x"41", x"50", x"53", x"3A", x"20",
        x"48", x"65", x"6C", x"6C", x"6F", x"20", x"57", x"6F",
        x"72", x"6C", x"64", x"21", x"20", x"31", x"32", x"33",
        x"34", x"35"
    );

    -- Example sine wave table: 200 samples, 8-bit values
    type sine_array_t is array(0 to 199) of std_logic_vector(7 downto 0);
    constant sine_wave : sine_array_t := (
       x"00",x"08",x"10",x"18",x"20",x"27",x"2F",x"36",x"3D",x"44",x"4B",x"51",x"57",x"5D",x"62",x"67",
x"6B",x"6F",x"73",x"76",x"79",x"7B",x"7D",x"7E",x"7F",x"7F",x"7F",x"7E",x"7D",x"7B",x"79",x"76",
x"73",x"6F",x"6B",x"67",x"62",x"5D",x"57",x"51",x"4B",x"44",x"3D",x"36",x"2F",x"27",x"20",x"18",
x"10",x"08",x"00",x"F8",x"F0",x"E8",x"E0",x"D9",x"D1",x"CA",x"C3",x"BC",x"B5",x"AF",x"A9",x"A3",
x"9E",x"99",x"95",x"91",x"8D",x"8A",x"87",x"85",x"83",x"82",x"81",x"81",x"81",x"82",x"83",x"85",
x"87",x"8A",x"8D",x"91",x"95",x"99",x"9E",x"A3",x"A9",x"AF",x"B5",x"BC",x"C3",x"CA",x"D1",x"D9",
x"E0",x"E8",x"F0",x"F8",x"00",x"08",x"10",x"18",x"20",x"27",x"2F",x"36",x"3D",x"44",x"4B",x"51",
x"57",x"5D",x"62",x"67",x"6B",x"6F",x"73",x"76",x"79",x"7B",x"7D",x"7E",x"7F",x"7F",x"7F",x"7E",
x"7D",x"7B",x"79",x"76",x"73",x"6F",x"6B",x"67",x"62",x"5D",x"57",x"51",x"4B",x"44",x"3D",x"36",
x"2F",x"27",x"20",x"18",x"10",x"08",x"00",x"F8",x"F0",x"E8",x"E0",x"D9",x"D1",x"CA",x"C3",x"BC",
x"B5",x"AF",x"A9",x"A3",x"9E",x"99",x"95",x"91",x"8D",x"8A",x"87",x"85",x"83",x"82",x"81",x"81",
x"81",x"82",x"83",x"85",x"87",x"8A",x"8D",x"91",x"95",x"99",x"9E",x"A3",x"A9",x"AF",x"B5",x"BC",
x"C3",x"CA",x"D1",x"D9",x"E0",x"E8",x"F0",x"F8"
    );

    signal trigger_in_prev : std_logic := '0';
    signal active          : std_logic := '0';
    signal counter         : unsigned(31 downto 0) := (others => '0');
    signal index           : integer range 0 to 200 := 0;  -- Supports both message and sine
    signal value_reg       : std_logic_vector(7 downto 0) := (others => '0');
    signal data_valid_reg  : std_logic := '0';

begin

    process(clk)
    begin
        if rising_edge(clk) then
            -- Rising edge detect
            if (trigger_in = '1' and trigger_in_prev = '0') then
                active <= '1';
                counter <= (others => '0');
                index <= 0;
                data_valid_reg <= '1';
                if mode_select = "00" then
                    value_reg <= ascii_message(0);
                elsif mode_select = "01" then
                    value_reg <= sine_wave(0);
                else
                    value_reg <= (others => '0'); -- default for unsupported modes
                    active <= '0';
                end if;
            else
                data_valid_reg <= '0';
                if active = '1' then
                    if counter = unsigned(period_value) then
                        counter <= (others => '0');

                        if mode_select = "00" then
                            if index < ascii_message'length - 1 then
                                index <= index + 1;
                                value_reg <= ascii_message(index + 1);
                                data_valid_reg <= '1';
                            else
                                active <= '0';
                                value_reg <= (others => '0');
                            end if;

                        elsif mode_select = "01" then
                            if index < 199 then
                                index <= index + 1;
                                value_reg <= sine_wave(index + 1);
                                data_valid_reg <= '1';
                            else
                                active <= '0';
                                value_reg <= (others => '0');
                            end if;

                        else
                            active <= '0';
                            value_reg <= (others => '0');
                        end if;

                    else
                        counter <= counter + 1;
                    end if;
                else
                    value_reg <= (others => '0');
                end if;
            end if;

            trigger_in_prev <= trigger_in;
        end if;
    end process;

    value <= value_reg;
    data_valid <= data_valid_reg;

end Behavioral;
