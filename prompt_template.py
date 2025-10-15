from dataclasses import dataclass

hold_set_pressure = """Hold Set Pressure: A event where pressure is increased and held steady to set the liner hanger.
        Visual pattern:
            * Start:
                - Pressure transitions from a relatively low, steady state to a linear increase.
                - Preceding period: pressure is stable.
            * In progress:
                - Phase 1: Pressure increases linearly.
                - Phase 2: Pressure is steady at a higher value. If the event `liner hanger set` happens, it is inside this phase.
            * End:
                - After liner hanger set, pressure transitions from a steady state to either a new linear increase or a linear decrease.
        Duration pattern:
            - 3–60 minutes (180–3600 rows).
        Noise pattern:
            - Expect possible sinusoidal noise in pressure, especially in progress.
        Sequential rules pattern:
            - All the occurrences of `hold set pressure` must occur before "Release Running Tool Confirmed".
            - During the entire job, `hold set pressure` may occur multiple times. However, before the next `liner hanger set` event, there should be a `shear ball seat` event.
            - If `liner hanger set` event happens, it must occur within a steady (held) phase of the `hold set pressure`.
            - A `hold set pressure event` should not contain an unsuccessful `liner hanger set` event.
            - At least one `hold set pressure` event should contain `liner hanger set` event."""

liner_hanger_set = """Liner Hanger Set: Setting of the liner hanger, detected via hookload and block height changes.
        Visual pattern:
            * Start:
                - Both hookload and block height shift from steady to quasi-simultaneous linear decrease.
            * In Progress
                - Hookload and block height decrease linearly and simultaneously.
            * End:
                - Both hookload and block height changes from linear decrease to steady at new, lower steady values. The change points should be observable in both block height and hookload at the same time. If one continues to decrease and the other becomes steady, it is not a successful set and should be ignored.
                - It is important to note that in the pressure steady phase of the `hold set pressure` event, the final values of hookload and block height must be lower than initial values and should not recover to a value equal or higher than the initial values. Otherwise, it is not a successful set and should be ignored.
        Duration pattern:
            - 0.5–10 minutes (30–600 rows).
        Sequential rules pattern:
            - It must occurs within a steady phase of the `hold set pressure`.
            - It must happen one time only during the entire job."""

shear_ball_seat = """Shear Ball Seat: A pressure event, marked by a rapid increase and subsequent drop in pressure.
        Visual pattern:
            * Start:
                - Pressure transitions from steady to a linear increase.
            * In Progress:
                - Pressure climbs to near the maximum observed value in the dataset, then drops precipitously to a low value.
            * End:
                - Pressure stabilizes at a low value.
        Duration pattern:
            - Typically <1 minute (≤60 rows).
        Sequential rules pattern:
            - Between two `hold set pressure` occurrences, there should be one and only one `shear ball seat` event. If multiple consecutive attempts between two `hold set pressure` occurrences, only the last one is a valid "shear ball seat" event."""

release_running_tool_confirmed = """Release Running Tool Confirmed: Removal of the running tool, identified by the synchronization and unsynchronization of the increases in block height and hookload.
        Visual pattern:
            * Start:
                - Both block height and hookload shift from steady to simultaneous linear increases.
            * In Progress:
                - There are three phases in this event.
                - Phase 1: Both block height and hookload increase linearly. They change simultaneously. Pay attention to the slope of the increase, because the slope of the increase in phase 1 need to be compared with the slope in phase 3 to determine if the event is successful.
                - Phase 2 (optional): Both block height and hookload become steady.
                - Phase 3: Block height increases linearly. However, hookload does not follow the increase of the block height as in phase 1. It is steady, increases slightly with a lower slope, or oscillates.
            * End:
                - Both block height and hookload become steady.
        Duration pattern:
            - 1–10 minutes (60–600 rows).
        Sequential rules pattern:
            - Occurs only once per job, always near the end.
            - Is the last or second-to-last event (if "Shear Ball Seat" follows)."""

liner_hanger_event_description = {
    "hold set pressure": hold_set_pressure,
    "liner hanger set": liner_hanger_set,
    "shear ball seat": shear_ball_seat,
    "release running tool confirmed": release_running_tool_confirmed
}

liner_hanger_job_description_iter4 = """
The dataset contains the surface measurement of liner hanger setting job during well completion in oil and gas industry. The objective is to install the liner hanger in oil well. 
The installation job involves monitoring and controlling several measurements to ensure a successful operation:
- Hookload reflects the pipe’s weight suspended from the rig.
- Pressure refers to inside string or annular pressures, essential for activating tools and verifying seals.
- Block Height measures the position of the traveling block, indicating the pipe's depth. This channel may contain spike noise.

A typical liner hanger job contains the four following steps. Each step needs to be performed successfully.
- hold set pressure: The setting of liner hanger needs high steady hydrolique pressure. Therefore, this step involves applying a predetermined pressure to hydraulically set the liner hanger. Pressure gauges are watched closely: a step increase indicates the hanger is setting starts. The operator holds the required pressure for a set period to ensure the full activation of the setting motor.
- liner hanger set: During the steady phase of hold set pressure, a simutainous decrease of hookload and block height indicate hanger setting, as the load is transfered to the well. If the hanger is not set successfully, the hookload may stop descrease and becomes steady while the block height continue to decrease. In this case, the operator will conduct another trial, after setting the pressure at a new steady value. The process will stop after the liner hanger is successfully set.
- shear ball seat: After the liner hanger is set, the operator will conduct a shear ball seat to ensure the liner hanger is securely seated in the well. The shear ball seat is a pressure event, marked by a rapid increase and subsequent drop in pressure. 
- release running tool confirmed: After the liner hanger is set, the operator will release the running tool. To confirm the release, the operator raise a bit the block height to see if the hookload increases at the same time. If the hookload does not increase, or the increase is not linear, the release is successful. The confirmation can be conducted before or after the shear ball seat.

The pattern of each successfully completed step/event can be summarized as follows:
    1. Hold Set Pressure  
-------------------  
Visual pattern:  
    * Start:  
        - Pressure transitions from a relatively low, steady state to a sustained, operator-driven linear increase.  
        - The start index is where pressure first departs from baseline and begins a significant, continuous rise (not a transient spike).  
        - Use a threshold on the pressure derivative (e.g., >X psi/row for at least N consecutive points) to define the start, to avoid noise or transient spikes.  
        - If multiple pressure holds exist, select the one that contains the successful 'liner hanger set' event. If no set is detected, use the first major pressure hold after the job begins.  
    * In progress:  
        - Phase 1: Pressure increases linearly (ramp-up).  
        - Phase 2: Pressure is held steady at a higher value for a significant duration. Define "steady" as pressure remaining within ±Y psi for at least Z points.  
        - Sinusoidal or minor oscillatory noise may be present in the steady phase.  
        - The 'liner hanger set' event must occur within the steady (held) phase of the 'hold set pressure' event for a successful event.  
    * End:  
        - The end index is the last point of the steady high-pressure phase, immediately before the intentional pressure release (sharp drop) or when pressure departs from the held value by more than a threshold (e.g., >100 psi over 5 consecutive points).  
        - Do not include the pressure drop itself or subsequent pressure holds unless they are part of the same continuous operation.  
  
Duration pattern:  
    - 3–60 minutes (180–3600 rows).  
  
Noise pattern:  
    - Expect possible sinusoidal noise in pressure, especially in progress.  
  
Sequential rules pattern:  
    - 'hold set pressure' must occur before 'release running tool confirmed'.  
    - Only one valid 'hold set pressure' event per job, as defined above.  
    - 'liner hanger set' event must occur within the steady (held) phase of the 'hold set pressure' for a successful event.  
    - A successful 'hold set pressure' event must contain a successful 'liner hanger set' event.  
    - 'shear ball seat' and 'release running tool confirmed' must occur after 'liner hanger set'.  
    - If multiple pressure holds exist, select the one that contains the successful 'liner hanger set' event (see below), and is followed by the 'shear ball seat' and 'release running tool confirmed' events. Ignore earlier pressure holds that do not lead to successful mechanical setting.
  
--------------------------------------------------  
  
2. Liner Hanger Set  
-------------------  
Visual pattern:  
    * Start:  
        - Both hookload and block height shift from steady to quasi-simultaneous linear decrease.  
        - The start index is the first point where both signals begin a sustained, simultaneous decrease (e.g., both derivatives negative and exceed minimum thresholds, such as -0.5 klbs/row for hookload and -0.05 ft/row for block height, for at least 3 consecutive points).  
        - The event must be detected within the steady phase of the first valid 'hold set pressure' event, as defined above.  
    * In progress:  
        - Hookload and block height decrease linearly and simultaneously. Minor lag (up to 10 points) or minor noise is acceptable.  
    * End:  
        - Both hookload and block height reach new, lower steady values.  
        - The end index is the first point where both signals remain within ±X units of their new steady values for at least Y consecutive points (e.g., ±1 klbs and ±0.1 ft for at least 5 points).  
        - If one continues to decrease and the other becomes steady, it is not a successful set and should be ignored.  
        - The final values of hookload and block height must be lower than initial values and should not recover to a value equal or higher than the initial values.  
  
Duration pattern:  
    - 0.5–10 minutes (30–600 rows).  
  
Sequential rules pattern:  
    - Must occur within the steady phase of the first valid 'hold set pressure' event.  
    - Only one valid 'liner hanger set' event per job.  
    - If multiple candidate 'liner hanger set' events are present, select the last one that is followed by the 'shear ball seat' and 'release running tool confirmed' events, and is contained within the final, successful 'hold set pressure' event.
    - If multiple pressure holds exist, only the one containing the simultaneous decrease in hookload and block height is valid.  
  
--------------------------------------------------  
  
3. Shear Ball Seat  
------------------  
Visual pattern:  
    * Start:  
        - Pressure transitions from steady to a rapid linear increase.  
        - The start index is where the first derivative of pressure exceeds a defined threshold above baseline (e.g., >X psi/row for at least N points, or 5x the standard deviation of noise in the steady phase).  
        - Use the first significant positive jump in the pressure derivative to mark the start; allow for a margin of ±2 points due to noise.  
    * In progress:  
        - Pressure climbs to near the maximum observed value in the dataset, then drops precipitously to a low value.  
    * End:  
        - Pressure stabilizes at a low value.  
        - The end index is the first point after the drop where pressure remains within a defined low range (e.g., ±20 psi) for a minimum duration (e.g., 5–10 points), and the derivative returns to near zero.  
  
Duration pattern:  
    - Typically <1 minute (≤60 rows).  
  
Sequential rules pattern:  
    - 'shear ball seat' event must occur after the 'liner hanger set' event.  
    - Only one valid 'shear ball seat' event per job, between two 'hold set pressure' events if multiple exist.  
  
Additional guidance:  
    - Use derivative analysis to precisely identify start and end boundaries.  
    - If multiple pressure spike/drop events are present, select the one with the largest amplitude and sharpest drop, occurring after the successful 'liner hanger set'.  
  
--------------------------------------------------  
  
4. Release Running Tool Confirmed  
---------------------------------  
Visual pattern:  
    * Start:  
        - The event window should start at the first index where both block height and hookload shift from steady to simultaneous linear increases (both derivatives positive for at least N points, with minimum slope thresholds).  
        - The operator initiates the confirmation (block height is intentionally raised from steady state, and hookload responds simultaneously).  
    * In progress:  
        - Phase 1: Both block height and hookload increase linearly and simultaneously (derivatives above threshold).  
        - Phase 2 (optional): Both block height and hookload become steady (derivatives near zero).  
        - Phase 3: Block height continues to increase, but hookload does not follow as in phase 1 (it is steady, increases slightly, or oscillates; derivative of hookload drops below threshold while block height remains above threshold).  
    * End:  
        - The event ends when both block height and hookload become steady again after the confirmation phase (derivatives near zero for at least 5 points).  
        - The window should be tightly bounded to the confirmation phase, not the entire operational sequence.  
        - Do not include preparatory or recovery phases or extended steady periods after the confirmation phase.  
  
Duration pattern:  
    - 1–10 minutes (60–600 rows).  
  
Sequential rules pattern:  
    - Occurs only once per job, always near the end.  
    - Is the last or second-to-last event (if 'shear ball seat' follows).  
  
Additional guidance:  
    - Ignore preparatory or recovery phases; focus on the confirmation phase only.  
    - Use minimum/maximum duration and value change constraints to avoid over-inclusion or late detections.  
    - If multiple candidate windows exist, select the one closest to the end of the job and after 'shear ball seat' (if present).  

Liner hanger setting job-specific tips for AI Agent:
- In general, the event "shear ball seat" has the most distinctive visual pattern. If your visual observation matches, you should identify the potential occurrences of "shear ball seat" first.
- Look for the potential occurrences of "liner hanger set" event preceding the potential occurrences of "shear ball seat". 
- If the "liner hanger set" event is found prededing the "shear ball seat", define the "hold set pressure" event that covers the "liner hanger set" event. 
- Validate the potential occurrences of the "share ball seat", "hold set pressure" and "liner hanger set" by the sequential rules.
- Each event must occur once and only once during the entire job.

General Tips for AI Agent:
- The starting and ending indices are typically characterized by change points in certain channels.
- Identify the event only when the full visual pattern is observed.
- Distinguish the SUCCESSFUL and UNSUCCESSFUL events.
- The visual pattern, duration pattern, noise pattern are the key to determine the potential occurrences of the event. 
- The sequential rules are the key information to determine the grouping, the order of identification and the verification of the events.
"""

liner_hanger_job_description_iter3 = """
The dataset contains the surface measurement of liner hanger setting job during well completion in oil and gas industry. The objective is to install the liner hanger in oil well. 
The installation job involves monitoring and controlling several measurements to ensure a successful operation:
- Hookload reflects the pipe’s weight suspended from the rig.
- Pressure refers to inside string or annular pressures, essential for activating tools and verifying seals.
- Block Height measures the position of the traveling block, indicating the pipe's depth. This channel may contain spike noise.

A typical liner hanger job contains the four following steps. Each step needs to be performed successfully.
- hold set pressure: The setting of liner hanger needs high steady hydrolique pressure. Therefore, this step involves applying a predetermined pressure to hydraulically set the liner hanger. Pressure gauges are watched closely: a step increase indicates the hanger is setting starts. The operator holds the required pressure for a set period to ensure the full activation of the setting motor.
- liner hanger set: During the steady phase of hold set pressure, a simutainous decrease of hookload and block height indicate hanger setting, as the load is transfered to the well. If the hanger is not set successfully, the hookload may stop descrease and becomes steady while the block height continue to decrease. In this case, the operator will conduct another trial, after setting the pressure at a new steady value. The process will stop after the liner hanger is successfully set.
- shear ball seat: After the liner hanger is set, the operator will conduct a shear ball seat to ensure the liner hanger is securely seated in the well. The shear ball seat is a pressure event, marked by a rapid increase and subsequent drop in pressure. 
- release running tool confirmed: After the liner hanger is set, the operator will release the running tool. To confirm the release, the operator raise a bit the block height to see if the hookload increases at the same time. If the hookload does not increase, or the increase is not linear, the release is successful. The confirmation can be conducted before or after the shear ball seat.

The pattern of each successfully completed step/event can be summarized as follows:
    1. Hold Set Pressure  
-------------------  
Visual pattern:  
    * Start:  
        - Pressure transitions from a relatively low, steady state to a sustained, operator-driven linear increase.  
        - The start index is where pressure first departs from baseline and begins a significant, continuous rise (not a transient spike).  
        - Use a threshold on the pressure derivative (e.g., >X psi/row for at least N consecutive points) to define the start, to avoid noise or transient spikes.  
        - If multiple pressure holds exist, select the one that contains the successful 'liner hanger set' event. If no set is detected, use the first major pressure hold after the job begins.  
    * In progress:  
        - Phase 1: Pressure increases linearly (ramp-up).  
        - Phase 2: Pressure is held steady at a higher value for a significant duration. Define "steady" as pressure remaining within ±Y psi for at least Z points.  
        - Sinusoidal or minor oscillatory noise may be present in the steady phase.  
        - The 'liner hanger set' event must occur within the steady (held) phase of the 'hold set pressure' event for a successful event.  
    * End:  
        - The end index is the last point of the steady high-pressure phase, immediately before the intentional pressure release (sharp drop) or when pressure departs from the held value by more than a threshold (e.g., >100 psi over 5 consecutive points).  
        - Do not include the pressure drop itself or subsequent pressure holds unless they are part of the same continuous operation.  
  
Duration pattern:  
    - 3–60 minutes (180–3600 rows).  
  
Noise pattern:  
    - Expect possible sinusoidal noise in pressure, especially in progress.  
  
Sequential rules pattern:  
    - 'hold set pressure' must occur before 'release running tool confirmed'.  
    - Only one valid 'hold set pressure' event per job, as defined above.  
    - 'liner hanger set' event must occur within the steady (held) phase of the 'hold set pressure' for a successful event.  
    - A successful 'hold set pressure' event must contain a successful 'liner hanger set' event.  
    - 'shear ball seat' and 'release running tool confirmed' must occur after 'liner hanger set'.
  
--------------------------------------------------  
  
2. Liner Hanger Set  
-------------------  
Visual pattern:  
    * Start:  
        - Both hookload and block height shift from steady to quasi-simultaneous linear decrease.  
        - The start index is the first point where both signals begin a sustained, simultaneous decrease (e.g., both derivatives negative and exceed minimum thresholds, such as -0.5 klbs/row for hookload and -0.05 ft/row for block height, for at least 3 consecutive points).  
        - The event must be detected within the steady phase of the first valid 'hold set pressure' event, as defined above.  
    * In progress:  
        - Hookload and block height decrease linearly and simultaneously. Minor lag (up to 10 points) or minor noise is acceptable.  
    * End:  
        - Both hookload and block height reach new, lower steady values.  
        - The end index is the first point where both signals remain within ±X units of their new steady values for at least Y consecutive points (e.g., ±1 klbs and ±0.1 ft for at least 5 points).  
        - If one continues to decrease and the other becomes steady, it is not a successful set and should be ignored.  
        - The final values of hookload and block height must be lower than initial values and should not recover to a value equal or higher than the initial values.  
  
Duration pattern:  
    - 0.5–10 minutes (30–600 rows).  
  
Sequential rules pattern:  
    - Must occur within the steady phase of the first valid 'hold set pressure' event.  
    - Only one valid 'liner hanger set' event per job.  
    - If multiple pressure holds exist, only the one containing the simultaneous decrease in hookload and block height is valid.  
  
--------------------------------------------------  
  
3. Shear Ball Seat  
------------------  
Visual pattern:  
    * Start:  
        - Pressure transitions from steady to a rapid linear increase.  
        - The start index is where the first derivative of pressure exceeds a defined threshold above baseline (e.g., >X psi/row for at least N points, or 5x the standard deviation of noise in the steady phase).  
        - Use the first significant positive jump in the pressure derivative to mark the start; allow for a margin of ±2 points due to noise.  
    * In progress:  
        - Pressure climbs to near the maximum observed value in the dataset, then drops precipitously to a low value.  
    * End:  
        - Pressure stabilizes at a low value.  
        - The end index is the first point after the drop where pressure remains within a defined low range (e.g., ±20 psi) for a minimum duration (e.g., 5–10 points), and the derivative returns to near zero.  
  
Duration pattern:  
    - Typically <1 minute (≤60 rows).  
  
Sequential rules pattern:  
    - 'shear ball seat' event must occur after the 'liner hanger set' event.  
    - Only one valid 'shear ball seat' event per job, between two 'hold set pressure' events if multiple exist.  
    
Additional guidance:  
    - Use derivative analysis to precisely identify start and end boundaries.  
    - If multiple pressure spike/drop events are present, select the one with the largest amplitude and sharpest drop, occurring after the successful 'liner hanger set'.  
  
--------------------------------------------------  
  
4. Release Running Tool Confirmed  
---------------------------------  
Visual pattern:  
    * Start:  
        - The event window should start at the first index where both block height and hookload shift from steady to simultaneous linear increases (both derivatives positive for at least N points, with minimum slope thresholds).  
        - The operator initiates the confirmation (block height is intentionally raised from steady state, and hookload responds simultaneously).  
    * In progress:  
        - Phase 1: Both block height and hookload increase linearly and simultaneously (derivatives above threshold).  
        - Phase 2 (optional): Both block height and hookload become steady (derivatives near zero).  
        - Phase 3: Block height continues to increase, but hookload does not follow as in phase 1 (it is steady, increases slightly, or oscillates; derivative of hookload drops below threshold while block height remains above threshold).  
    * End:  
        - The event ends when both block height and hookload become steady again after the confirmation phase (derivatives near zero for at least 5 points).  
        - The window should be tightly bounded to the confirmation phase, not the entire operational sequence.  
        - Do not include preparatory or recovery phases or extended steady periods after the confirmation phase.  
  
Duration pattern:  
    - 1–10 minutes (60–600 rows).  
  
Sequential rules pattern:  
    - Occurs only once per job, always near the end.  
    - Is the last or second-to-last event (if 'shear ball seat' follows).  
  
Additional guidance:  
    - Ignore preparatory or recovery phases; focus on the confirmation phase only.  
    - Use minimum/maximum duration and value change constraints to avoid over-inclusion or late detections.  
    - If multiple candidate windows exist, select the one closest to the end of the job and after 'shear ball seat' (if present).  

Liner hanger setting job-specific tips for AI Agent:
- In general, the event "shear ball seat" has the most distinctive visual pattern. If your visual observation matches, you should identify the potential occurrences of "shear ball seat" first.
- Look for the potential occurrences of "liner hanger set" event preceding the potential occurrences of "shear ball seat". 
- If the "liner hanger set" event is found prededing the "shear ball seat", define the "hold set pressure" event that covers the "liner hanger set" event. 
- Validate the potential occurrences of the "share ball seat", "hold set pressure" and "liner hanger set" by the sequential rules.
- Each event must occur once and only once during the entire job.

General Tips for AI Agent:
- The starting and ending indices are typically characterized by change points in certain channels.
- Identify the event only when the full visual pattern is observed.
- Distinguish the SUCCESSFUL and UNSUCCESSFUL events.
- The visual pattern, duration pattern, noise pattern are the key to determine the potential occurrences of the event. 
- The sequential rules are the key information to determine the grouping, the order of identification and the verification of the events.
"""

liner_hanger_job_description_iter2_2 = """
The dataset contains the surface measurement of liner hanger setting job during well completion in oil and gas industry. The objective is to install the liner hanger in oil well. 
The installation job involves monitoring and controlling several measurements to ensure a successful operation:
- Hookload reflects the pipe’s weight suspended from the rig.
- Pressure refers to inside string or annular pressures, essential for activating tools and verifying seals.
- Block Height measures the position of the traveling block, indicating the pipe's depth. This channel may contain spike noise.

A typical liner hanger job contains the four following steps. Each step needs to be performed successfully.
- hold set pressure: The setting of liner hanger needs high steady hydrolique pressure. Therefore, this step involves applying a predetermined pressure to hydraulically set the liner hanger. Pressure gauges are watched closely: a step increase indicates the hanger is setting starts. The operator holds the required pressure for a set period to ensure the full activation of the setting motor.
- liner hanger set: During the steady phase of hold set pressure, a simutainous decrease of hookload and block height indicate hanger setting, as the load is transfered to the well. If the hanger is not set successfully, the hookload may stop descrease and becomes steady while the block height continue to decrease. In this case, the operator will conduct another trial, after setting the pressure at a new steady value. The process will stop after the liner hanger is successfully set.
- shear ball seat: After the liner hanger is set, the operator will conduct a shear ball seat to ensure the liner hanger is securely seated in the well. The shear ball seat is a pressure event, marked by a rapid increase and subsequent drop in pressure. 
- release running tool confirmed: After the liner hanger is set, the operator will release the running tool. To confirm the release, the operator raise a bit the block height to see if the hookload increases at the same time. If the hookload does not increase, or the increase is not linear, the release is successful. The confirmation can be conducted before or after the shear ball seat.

The pattern of each successfully completed step/event can be summarized as follows:
    1. Hold Set Pressure:
        - Visual pattern:
            * Start:
                - Pressure transitions from a relatively low, steady state to a sustained, operator-driven linear increase. The start index is where pressure first departs from baseline and begins a significant, continuous rise (not a transient spike).
            * In progress:
                - Phase 1: Pressure increases linearly.
                - Phase 2: Pressure is held steady at a higher value for a significant duration. The 'liner hanger set' event must occur within this steady phase.
            * End:
                - The end index is where pressure is intentionally released (sharp drop) or transitions to a new operational phase. Do not include subsequent pressure holds unless they are part of the same continuous operation.
        - If multiple pressure holds exist, select the one that contains the successful 'liner hanger set' event (see below), and is followed by the 'shear ball seat' and 'release running tool confirmed' events. Ignore earlier pressure holds that do not lead to successful mechanical setting.
        - Duration pattern:
            - 3–60 minutes (180–3600 rows).
        - Noise pattern:
            - Expect possible sinusoidal noise in pressure, especially in progress.
        - Sequential rules pattern:
            - 'hold set pressure' must occur before 'release running tool confirmed'.
            - Only one valid 'hold set pressure' event per job, defined as above.
            - 'liner hanger set' event must occur within the steady (held) phase of the 'hold set pressure'.
            - A successful 'hold set pressure' event must contain a successful 'liner hanger set' event.
            - 'shear ball seat' and 'release running tool confirmed' must occur after 'liner hanger set'.

    2. Liner Hanger Set:
        - Visual pattern:
            * Start:
                - Both hookload and block height shift from steady to quasi-simultaneous linear decrease.
                - The event must be detected within the steady phase of the final, successful 'hold set pressure' event, as defined above.
            * In Progress:
                - Hookload and block height decrease linearly and simultaneously.
            * End:
                - Both hookload and block height reach new, lower steady values. The change points should be observable in both channels at the same time. If one continues to decrease and the other becomes steady, it is not a successful set and should be ignored.
                - The final values of hookload and block height must be lower than initial values and should not recover to a value equal or higher than the initial values.
        - If multiple candidate 'liner hanger set' events are present, select the last one that is followed by the 'shear ball seat' and 'release running tool confirmed' events, and is contained within the final, successful 'hold set pressure' event.
        - Duration pattern:
            - 0.5–10 minutes (30–600 rows).
        - Sequential rules pattern:
            - Must occur within the steady phase of the final, successful 'hold set pressure' event.
            - Only one valid 'liner hanger set' event per job.
            - If multiple pressure holds exist, only the one containing the simultaneous decrease in hookload and block height is valid.

    3. Shear Ball Seat:
        - Visual pattern:
            * Start:
                - Pressure transitions from steady to a rapid linear increase. The start index is where the first derivative of pressure exceeds a defined threshold above baseline.
            * In Progress:
                - Pressure climbs to near the maximum observed value in the dataset, then drops precipitously to a low value.
            * End:
                - Pressure stabilizes at a low value. The end index is where pressure remains within a defined range (e.g., ±5 psi) for a minimum duration (e.g., 5–10 points).
        - Use derivative analysis to precisely identify start and end boundaries. For stabilization, define a window (e.g., 10 points) where the standard deviation of pressure is below a small threshold (e.g., 2% of the drop magnitude).
        - Duration pattern:
            - Typically <1 minute (≤60 rows).
        - Sequential rules pattern:
            - 'shear ball seat' event must occur after the 'liner hanger set' event.
            - Only one valid 'shear ball seat' event per job, between two 'hold set pressure' events if multiple exist.

    4. Release Running Tool Confirmed:
        - Visual pattern:
            * Start:
                - The event window should start at the first index where block height departs from a steady baseline and both block height and hookload increase simultaneously with a slope above a defined threshold (e.g., 10% of the maximum observed slope in the job).
            * In Progress:
                - Phase 1: Both block height and hookload increase linearly and simultaneously.
                - Phase 2 (optional): Both block height and hookload become steady.
                - Phase 3: Block height continues to increase, but hookload does not follow as in phase 1 (it is steady, increases slightly, or oscillates).
            * End:
                - The event ends at the first index after phase 3 where both block height and hookload remain steady (standard deviation below a small threshold, e.g., 0.05 ft for block height, 1 klb for hookload) for at least 10 points.
        - Ignore preparatory or recovery phases by requiring a minimum duration of simultaneous increase and a check for return to steady state.
        - Duration pattern:
            - 1–10 minutes (60–600 rows).
        - Sequential rules pattern:
            - Occurs only once per job, always near the end.
            - Is the last or second-to-last event (if 'shear ball seat' follows).
        - Additional guidance:
            - Use explicit slope and steady-state criteria for start/end to tightly bound the event window.

Liner hanger setting job-specific tips for AI Agent:
- In general, the event "shear ball seat" has the most distinctive visual pattern. If your visual observation matches, you should identify the potential occurrences of "shear ball seat" first.
- Look for the potential occurrences of "liner hanger set" event preceding the potential occurrences of "shear ball seat". 
- If the "liner hanger set" event is found prededing the "shear ball seat", define the "hold set pressure" event that covers the "liner hanger set" event. 
- Validate the potential occurrences of the "share ball seat", "hold set pressure" and "liner hanger set" by the sequential rules.
- Each event must occur once and only once during the entire job.

General Tips for AI Agent:
- The starting and ending indices are typically characterized by change points in certain channels.
- Identify the event only when the full visual pattern is observed.
- Distinguish the SUCCESSFUL and UNSUCCESSFUL events.
- The visual pattern, duration pattern, noise pattern are the key to determine the potential occurrences of the event. 
- The sequential rules are the key information to determine the grouping, the order of identification and the verification of the events.
"""

liner_hanger_job_description_iter2_1 = """
The dataset contains the surface measurement of liner hanger setting job during well completion in oil and gas industry. The objective is to install the liner hanger in oil well. 
The installation job involves monitoring and controlling several measurements to ensure a successful operation:
- Hookload reflects the pipe’s weight suspended from the rig.
- Pressure refers to inside string or annular pressures, essential for activating tools and verifying seals.
- Block Height measures the position of the traveling block, indicating the pipe's depth. This channel may contain spike noise.

A typical liner hanger job contains the four following steps. Each step needs to be performed successfully.
- hold set pressure: The setting of liner hanger needs high steady hydrolique pressure. Therefore, this step involves applying a predetermined pressure to hydraulically set the liner hanger. Pressure gauges are watched closely: a step increase indicates the hanger is setting starts. The operator holds the required pressure for a set period to ensure the full activation of the setting motor.
- liner hanger set: During the steady phase of hold set pressure, a simutainous decrease of hookload and block height indicate hanger setting, as the load is transfered to the well. If the hanger is not set successfully, the hookload may stop descrease and becomes steady while the block height continue to decrease. In this case, the operator will conduct another trial, after setting the pressure at a new steady value. The process will stop after the liner hanger is successfully set.
- shear ball seat: After the liner hanger is set, the operator will conduct a shear ball seat to ensure the liner hanger is securely seated in the well. The shear ball seat is a pressure event, marked by a rapid increase and subsequent drop in pressure. 
- release running tool confirmed: After the liner hanger is set, the operator will release the running tool. To confirm the release, the operator raise a bit the block height to see if the hookload increases at the same time. If the hookload does not increase, or the increase is not linear, the release is successful. The confirmation can be conducted before or after the shear ball seat.

The pattern of each successfully completed step/event can be summarized as follows:
    1. Hold Set Pressure:
        - Visual pattern:
            * Start:
                - Pressure transitions from a relatively low, steady state to a sustained, operator-driven linear increase. The start index is where pressure first departs from baseline and begins a significant, continuous rise (not a transient spike).
                - If multiple pressure holds exist, the correct event is the first major pressure hold after the job begins, or the one that contains the 'liner hanger set' event.
            * In progress:
                - Phase 1: Pressure increases linearly.
                - Phase 2: Pressure is held steady at a higher value for a significant duration. The 'liner hanger set' event must occur within this steady phase.
            * End:
                - The end index is where pressure is intentionally released (sharp drop) or transitions to a new operational phase. Do not include subsequent pressure holds unless they are part of the same continuous operation.
        - Duration pattern:
            - 3–60 minutes (180–3600 rows).
        - Noise pattern:
            - Expect possible sinusoidal noise in pressure, especially in progress.
        - Sequential rules pattern:
            - 'hold set pressure' must occur before 'release running tool confirmed'.
            - Only one valid 'hold set pressure' event per job, defined as above.
            - 'liner hanger set' event must occur within the steady (held) phase of the 'hold set pressure'.
            - A successful 'hold set pressure' event must contain a successful 'liner hanger set' event.
            - 'shear ball seat' and 'release running tool confirmed' must occur after 'liner hanger set'.

    2. Liner Hanger Set:
        - Visual pattern:
            * Start:
                - Both hookload and block height shift from steady to quasi-simultaneous linear decrease.
                - The event must be detected within the steady phase of the first valid 'hold set pressure' event, as defined above.
            * In Progress:
                - Hookload and block height decrease linearly and simultaneously.
            * End:
                - Both hookload and block height reach new, lower steady values. The change points should be observable in both channels at the same time. If one continues to decrease and the other becomes steady, it is not a successful set and should be ignored.
                - The final values of hookload and block height must be lower than initial values and should not recover to a value equal or higher than the initial values.
        - Duration pattern:
            - 0.5–10 minutes (30–600 rows).
        - Sequential rules pattern:
            - Must occur within the steady phase of the first valid 'hold set pressure' event.
            - Only one valid 'liner hanger set' event per job.
            - If multiple pressure holds exist, only the one containing the simultaneous decrease in hookload and block height is valid.

    3. Shear Ball Seat:
        - Visual pattern:
            * Start:
                - Pressure transitions from steady to a rapid linear increase. The start index is where the first derivative of pressure exceeds a defined threshold above baseline.
            * In Progress:
                - Pressure climbs to near the maximum observed value in the dataset, then drops precipitously to a low value.
            * End:
                - Pressure stabilizes at a low value. The end index is where pressure remains within a defined range for a minimum duration (e.g., 5–10 points).
        - Duration pattern:
            - Typically <1 minute (≤60 rows).
        - Sequential rules pattern:
            - 'shear ball seat' event must occur after the 'liner hanger set' event.
            - Only one valid 'shear ball seat' event per job, between two 'hold set pressure' events if multiple exist.
        - Additional guidance:
            - Use derivative analysis to precisely identify start and end boundaries.

    4. Release Running Tool Confirmed:
        - Visual pattern:
            * Start:
                - The event window should start at the first index where the operator initiates the confirmation (block height is intentionally raised from steady state, and hookload responds simultaneously).
            * In Progress:
                - Phase 1: Both block height and hookload increase linearly and simultaneously.
                - Phase 2 (optional): Both block height and hookload become steady.
                - Phase 3: Block height continues to increase, but hookload does not follow as in phase 1 (it is steady, increases slightly, or oscillates).
            * End:
                - The event ends when both block height and hookload become steady again after the confirmation phase.
                - The window should be tightly bounded to the confirmation phase, not the entire operational sequence.
        - Duration pattern:
            - 1–10 minutes (60–600 rows).
        - Sequential rules pattern:
            - Occurs only once per job, always near the end.
            - Is the last or second-to-last event (if 'shear ball seat' follows).
        - Additional guidance:
            - Ignore preparatory or recovery phases; focus on the confirmation phase only.
            - Use minimum/maximum duration constraints to avoid over-inclusion.
Liner hanger setting job-specific tips for AI Agent:
- In general, the event "shear ball seat" has the most distinctive visual pattern. If your visual observation matches, you should identify the potential occurrences of "shear ball seat" first.
- Look for the potential occurrences of "liner hanger set" event preceding the potential occurrences of "shear ball seat". 
- If the "liner hanger set" event is found prededing the "shear ball seat", define the "hold set pressure" event that covers the "liner hanger set" event. 
- Validate the potential occurrences of the "share ball seat", "hold set pressure" and "liner hanger set" by the sequential rules.
- Each event must occur once and only once during the entire job.

General Tips for AI Agent:
- The starting and ending indices are typically characterized by change points in certain channels.
- Identify the event only when the full visual pattern is observed.
- Distinguish the SUCCESSFUL and UNSUCCESSFUL events.
- The visual pattern, duration pattern, noise pattern are the key to determine the potential occurrences of the event. 
- The sequential rules are the key information to determine the grouping, the order of identification and the verification of the events.
"""

liner_hanger_job_description_iter2 = """
The dataset contains the surface measurement of liner hanger setting job during well completion in oil and gas industry. The objective is to install the liner hanger in oil well. 
The installation job involves monitoring and controlling several measurements to ensure a successful operation:
- Hookload reflects the pipe’s weight suspended from the rig.
- Pressure refers to inside string or annular pressures, essential for activating tools and verifying seals.
- Block Height measures the position of the traveling block, indicating the pipe's depth. This channel may contain spike noise.

A typical liner hanger job contains the four following steps. Each step needs to be performed successfully.
- hold set pressure: The setting of liner hanger needs high steady hydrolique pressure. Therefore, this step involves applying a predetermined pressure to hydraulically set the liner hanger. Pressure gauges are watched closely: a step increase indicates the hanger is setting starts. The operator holds the required pressure for a set period to ensure the full activation of the setting motor.
- liner hanger set: During the steady phase of hold set pressure, a simutainous decrease of hookload and block height indicate hanger setting, as the load is transfered to the well. If the hanger is not set successfully, the hookload may stop descrease and becomes steady while the block height continue to decrease. In this case, the operator will conduct another trial, after setting the pressure at a new steady value. The process will stop after the liner hanger is successfully set.
- shear ball seat: After the liner hanger is set, the operator will conduct a shear ball seat to ensure the liner hanger is securely seated in the well. The shear ball seat is a pressure event, marked by a rapid increase and subsequent drop in pressure. 
- release running tool confirmed: After the liner hanger is set, the operator will release the running tool. To confirm the release, the operator raise a bit the block height to see if the hookload increases at the same time. If the hookload does not increase, or the increase is not linear, the release is successful. The confirmation can be conducted before or after the shear ball seat.

The pattern of each successfully completed step/event can be summarized as follows:
    1. Hold Set Pressure: A event where pressure is increased and held steady to set the liner hanger.
        Visual pattern:
            * Start:
                - Pressure transitions from a relatively low, steady state to a linear increase.
                - Preceding period: pressure is stable.
            * In progress:
                - Phase 1: Pressure increases linearly.
                - Phase 2: Pressure is steady at a higher value. If the event `liner hanger set` happens, it is inside this phase.
            * End:
                - After liner hanger set, pressure transitions from a steady state to either a new linear increase or a linear decrease.
        Duration pattern:
            - 3–60 minutes (180–3600 rows).
        Noise pattern:
            - Expect possible sinusoidal noise in pressure, especially in progress.
        Sequential rules pattern:
            - `hold set pressure` must occur before "Release Running Tool Confirmed".
            - During the entire job, `hold set pressure` one occur only once, which is the step increase that covers the successful liner hanger set.
            - `liner hanger set` event must occur within a steady (held) phase of the `hold set pressure`.
            - A successful `hold set pressure event` should contain a successful `liner hanger set` event.
            - `shear ball seat` and `release running tool confirmed` event must occur after the `liner hanger set` event.
    2. Liner Hanger Set: Setting of the liner hanger, detected via hookload and block height changes.
        Visual pattern:
            * Start:
                - Both hookload and block height shift from steady to quasi-simultaneous linear decrease.
            * In Progress
                - Hookload and block height decrease linearly and simultaneously.
            * End:
                - Both hookload and block height changes from linear decrease to steady at new, lower steady values. The change points should be observable in both block height and hookload at the same time. If one continues to decrease and the other becomes steady, it is not a successful set and should be ignored.
                - It is important to note that in the pressure steady phase of the `hold set pressure` event, the final values of hookload and block height must be lower than initial values and should not recover to a value equal or higher than the initial values. Otherwise, it is not a successful set and should be ignored.
        Duration pattern:
            - 0.5–10 minutes (30–600 rows).
        Sequential rules pattern:
            - It must occurs within a steady phase of the `hold set pressure`.
            - It must happen one time only during the entire job.
            - This is the most important event to detect. All the other events are based on the successful `liner hanger set` event.
    3. Shear Ball Seat: A pressure event, marked by a rapid increase and subsequent drop in pressure.
        Visual pattern:
            * Start:
                - Pressure transitions from steady to a linear increase.
            * In Progress:
                - Pressure climbs to near the maximum observed value in the dataset, then drops precipitously to a low value.
            * End:
                - Pressure stabilizes at a low value.
        Duration pattern:
            - Typically <1 minute (≤60 rows).
        Sequential rules pattern:
            - `shear ball seat` event must occur posterior to the `liner hanger set` event.
    4. Release Running Tool Confirmed: Removal of the running tool, identified by the synchronization and unsynchronization of the increases in block height and hookload.
        Visual pattern:
            * Start:
                - Both block height and hookload shift from steady to simultaneous linear increases.
            * In Progress:
                - There are three phases in this event.
                - Phase 1: Both block height and hookload increase linearly. They change simultaneously. Pay attention to the slope of the increase, because the slope of the increase in phase 1 need to be compared with the slope in phase 3 to determine if the event is successful.
                - Phase 2 (optional): Both block height and hookload become steady.
                - Phase 3: Block height increases linearly. However, hookload does not follow the increase of the block height as in phase 1. It is steady, increases slightly with a lower slope, or oscillates.
            * End:
                - Both block height and hookload become steady.
        Duration pattern:
            - 1–10 minutes (60–600 rows).
        Sequential rules pattern:
            - Occurs only once per job, always near the end.
            - Is the last or second-to-last event (if "Shear Ball Seat" follows).
            - After `liner hanger set`, it might take a while before the operator the conduct `release running tool confirmed` event. During this period, the operator may conduct other pressure events. The block height should remain mostly constant with minor spike noise.

Liner hanger setting job-specific tips for AI Agent:
- In general, the event "shear ball seat" has the most distinctive visual pattern. If your visual observation matches, you should identify the potential occurrences of "shear ball seat" first.
- Look for the potential occurrences of "liner hanger set" event preceding the potential occurrences of "shear ball seat". 
- If the "liner hanger set" event is found prededing the "shear ball seat", define the "hold set pressure" event that covers the "liner hanger set" event. 
- Validate the potential occurrences of the "share ball seat", "hold set pressure" and "liner hanger set" by the sequential rules.
- Each event must occur once and only once during the entire job.

General Tips for AI Agent:
- The starting and ending indices are typically characterized by change points in certain channels.
- Identify the event only when the full visual pattern is observed.
- Distinguish the SUCCESSFUL and UNSUCCESSFUL events.
- The visual pattern, duration pattern, noise pattern are the key to determine the potential occurrences of the event. 
- The sequential rules are the key information to determine the grouping, the order of identification and the verification of the events.
"""

liner_hanger_job_description_iter1 = """
The dataset contains the surface measurement of liner hanger setting job during well completion in oil and gas industry.
- Measurements: hookload, block height, pressure

The liner hanger setting job is composed of the following steps/events, which can be traced from the measurements:
    1. {hold_set_pressure}
    2. {liner_hanger_set}
    3. {shear_ball_seat}
    4. {release_running_tool_confirmed}

Liner hanger setting job-specific tips for AI Agent:
- In general, the event "shear ball seat" has the most distinctive visual pattern. If your visual observation matches, you should identify the potential occurrences of "shear ball seat" first.
- Look for the potential occurrences of "liner hanger set" event preceding the potential occurrences of "shear ball seat". 
- If the "liner hanger set" event is found prededing the "shear ball seat", define the "hold set pressure" event that covers the "liner hanger set" event.
- If no "liner hanger set" event is found, look for potential occurrences of "hold set pressure" preceding the potential occurrences of "shear ball seat". 
- Validate the potential occurrences of the "share ball seat", "hold set pressure" and "liner hanger set" by the sequential rules.

General Tips for AI Agent:
- The starting and ending indices are typically characterized by change points in certain channels.
- Identify the event only when the full visual pattern is observed.
- The visual pattern, duration pattern, noise pattern are the key to determine the potential occurrences of the event. 
- The sequential rules are the key information to determine the grouping, the order of identification and the verification of the events.
""".format(
    hold_set_pressure=hold_set_pressure,
    liner_hanger_set=liner_hanger_set,
    shear_ball_seat=shear_ball_seat,
    release_running_tool_confirmed=release_running_tool_confirmed
)

liner_hanger_job_narrative = """
The liner hanger job's objective is to install the liner hanger in oil well. 
The installation job involves monitoring and controlling several measurements to ensure a successful operation:
- Hookload reflects the pipe’s weight suspended from the rig.
- Pressure refers to inside string or annular pressures, essential for activating tools and verifying seals.
- Block Height measures the position of the traveling block, indicating the pipe's depth.

A typical liner hanger job contains the four following steps. Each step needs to be performed successfully.
- hold set pressure: The setting of liner hanger needs high steady hydrolique pressure. Therefore, this step involves applying a predetermined pressure to hydraulically set the liner hanger. Pressure gauges are watched closely: a step increase indicates the hanger is setting starts. The operator holds the required pressure for a set period to ensure the full activation of the setting motor.
- liner hanger set: During the steady phase of hold set pressure, a simutainous decrease of hookload and block height indicate hanger setting, as the load is transfered to the well. If the hanger is not set successfully, the hookload may stop descrease and becomes steady while the block height continue to decrease. In this case, the operator will conduct another trial, after setting the pressure at a new steady value. The process will stop after the liner hanger is successfully set.
- shear ball seat: After the liner hanger is set, the operator will conduct a shear ball seat to ensure the liner hanger is securely seated in the well. The shear ball seat is a pressure event, marked by a rapid increase and subsequent drop in pressure. The operator will conduct the shear ball seat after the liner hanger is set.
- release running tool confirmed: After the shear ball seat, the operator will release the running tool. To confirm the release, the operator raise a bit the block height to see if the hookload increases at the same time. If the hookload does not increase, or the increase is not linear, the release is successful. 
"""

liner_hanger_job_description = liner_hanger_job_description_iter4

PLANNER_SYSTEM_PROMPT = """You are an AI-powered PLANNER agent specialized in signal processing and strategic planning.

You will be provided with:
- A time-series dataset, which is collected from various sensors and prepresent different physical quantities over time during industrial operation. 
During the operation, a series of events was undertaken. Each event can be identified from the time-series based on its own pattern.
- A description of events pattern
- A list of tools to plot the dataset

The user's objective is to identify the starting and ending indicies of each event.
Since the time-series dataset can be large, and the list of tasks/event can be long, your task is to perform high-level global analysis of the entire time-series dataset, plan the event identification and verification process, divide the process into subtasks.
The detailed event identification and verification will be performed by two specialized AI-powered agents following your guidance: an IDENTIFIER agent for event identification tasks and a VALIDATOR agent for event verification tasks. You need to provide meaningful instructions for each subtask so that these agents can identify or verify the events in each subtasks more efficiently.
The agents will undertake the subtasks sequentially.

Your role is to:
1. Perform high-level global analysis of the entire time-series dataset
2. Create a strategic event identification plan. To get a good plan, based on the visualization and the pattern descritpion, you should consider:
    - Ordering the events by the distinctiveness of their pattern and visual clarity.
    - Grouping the events that have strong interdependencies. The identification of the event group should be performed together in one subtask by the IDENTIFIER agent.
    - Providing a potential window ranges that covers the interdependent events along with clear instructions for the IDENTIFIER agent to start each subtask.
    - **IMPORTANT:** When creating IdentifierTask instructions, NEVER include specific window ranges, index numbers, or time ranges in the instructions. These must be provided separately in the potential_windows field. Instructions should focus only on visual patterns, characteristics, and identification guidance.
    - Assign a verification task after a certain round of identification tasks to ensure the identification result matches the sequential rules.
    - Before giving the final results, make sure all the results that need verification have been verified.
3. Dynamically update the plan based on the result of the subtasks given by the IDENTIFIER and VALIDATOR agents. You can adjust/add/modify the identification or verification tasks in the plan iteratively for the subtask to be taken after you get the identification results of certain events from these agents.
4. Coordinate the overall identification process.

YOUR TOOLS (LIMITED TO GLOBAL ANALYSIS):
- `plot_window_with_window_size(mid_idx, window_size, y_zoomed: bool)`: Examine specific sections with controlled window sizes
    - `mid_idx`: integer, center index of the window.
    - `window_size`: integer, number of data points in the window.
    - `y_zoomed`: boolean. If True, y-axis is scaled to the data in the window; if False, y-axis covers the full dataset range.

STRATEGIC APPROACH:
2. Use `plot_window_with_window_size()` to examine specific regions you identify as interesting. Since you are making gross analysis to provide braod assessment, the window size should be broad enough to cover the events.
3. Order by distinctiveness: identify the most visually obvious patterns first
4. Group interdependent events together (e.g., events that must occur in sequence)
5. The results in the previous steps may not be accurate. Therefore, for the events having interdependencies, you should instruct the IDENTIFIER agent to mainly focus on the visual pattern and identify all the potential occurrences. After the interdependent events are identified, you need to add verification step to validate the occurrences by the sequential rules.
6. Provide window hints and specific analysis instructions to guide the IDENTIFIER and VALIDATOR agents on where to look into. The window hint should be broad enough to cover the event. These agents will make fine-grained analysis within the window.
   **CRITICAL:** When creating instructions for IDENTIFIER tasks, do NOT include specific window ranges, index numbers, or time ranges in the 'instructions' field. Window ranges must be provided separately in the 'potential_windows' field. Instructions should only contain pattern descriptions, visual characteristics, and identification guidance.
7. When tools are needed, add a separator '***' between explaination and tool calling.
8. Call one tool at one time
9. Always update the plan before assigning task to the IDENTIFIER and VALIDATOR agents.
"""

PLANNER_INIT_MESSAGE = """
PLANNER TASK ASSIGNMENT
=======================

EVENT PATTERNS TO IDENTIFY:
{patterns}

DATASET OVERVIEW:
{statistics}

TARGET EVENTS:
{events_list}

YOUR PLANNING MISSION:
1. Analyze the complete dataset to understand global patterns
2. Create a strategic plan for event identification and verification
3. Order events by distinctiveness and visual clarity
4. Group interdependent events together
5. Provide specific windows and instructions for the worker agent to identify and verify the events
6. Coordinate the overall identification and verification process

STRATEGIC APPROACH:
- Identify most visually obvious patterns first from global analysis of the plot of the entire data
- Group events that must occur in sequence
- For the events having interdependencies, you should first identify all the potential occurrences that satisfy the visual pattern. After the interdependent events are identified, you need to add verification step to validate the occurrences by the sequential rules.
- Provide approximate windows for worker to identify and verify the events
- Update plan based on worker results
- Ensure comprehensive coverage of all target events

REMEMBER:
- Focus on high-level strategy and coordination
- Provide clear, actionable instructions to workers
- **CRITICAL:** When creating IdentifierTask instructions, NEVER include specific window ranges or index numbers in the instructions field. Window information must be provided separately in the potential_windows field and will be processed before reaching the identifier agent.
- Use structured communication formats
- Monitor progress and adjust plans as needed
"""

WORKER_SYSTEM_PROMPT = """You are an AI-powered WORKER agent. Your job is to precisely identify and verify the start and end indices of specific events in a time-series dataset, based on instructions from a PLANNER agent and using a suite of analysis tools.

You will receive:
- A time-series dataset collected from multiple sensors, representing different physical quantities over time during an industrial operation.
- Descriptions of the patterns that define each event.
- Instructions from the PLANNER agent specifying which events to identify and pattern recognition guidance. NOTE: These instructions will NOT contain correct specific window ranges or index numbers.
- Separate window information that has been processed and refined specifically for your analysis.
- Access to a set of tools for plotting, navigating, and inspecting the data.

YOUR RESPONSIBILITIES:
1. Carefully read the event identification and verification tasks from the PLANNER agent.
2. Use the available tools to analyze the data and accurately determine the start and end indices for each assigned event.
3. Report your findings back to the PLANNER, including confidence measures and supporting evidence.

TOOLKIT (refer to the function signatures and parameter types for correct usage):

- Plotting Tools:
    - `plot_window(start: int, end: int, y_zoomed: bool)`: Plots a window of the data from index `start` (inclusive) to `end` (exclusive). 
        - `start`: integer, starting index of the window.
        - `end`: integer, ending index (exclusive).
        - `y_zoomed`: boolean. If True, y-axis is scaled to the data in the window; if False, y-axis covers the full dataset range.
        *Best use*: Inspect a specific region of the data in detail, with control over y-axis scaling for local or global context.
    - `plot_window_with_window_size(mid_idx: int, window_size: int, y_zoomed: bool)`: Plots a window centered at `mid_idx` with total width `window_size`.
        - `mid_idx`: integer, center index of the window.
        - `window_size`: integer, number of data points in the window.
        - `y_zoomed`: boolean, as above.
        *Best use*: Focus on a region around a suspected transition, with adjustable context and zoom.

- Navigation Tools (operate on the current plotted window):
    - `plot_left()`: Moves the current window left by 3/4 of its width. No parameters.
        *Best use*: Explore earlier data or shift the window to the left to find the start of an event.
    - `plot_right()`: Moves the current window right by 3/4 of its width. No parameters.
        *Best use*: Explore later data or shift the window to the right to find the end of an event.
    - `plot_zoom_in_x()`: Halves the current window width, centered on the same point. No parameters.
        *Best use*: Zoom in for a more detailed temporal view, useful for pinpointing event boundaries.
    - `plot_zoom_out_x()`: Doubles the current window width, centered on the same point. No parameters.
        *Best use*: Zoom out for broader context, useful for understanding the surroundings of an event.

- Investigation Tools (operate on the current plotted window):
    - `plot_derivative(channels: List[str])`: Plots the selected channels and their first derivatives.
        - `channels`: list of strings, each the name of a channel/column to plot.
        *Best use*: Detect inflection points, rapid changes, or oscillatory behavior in specific channels.
    - `plot_second_derivative(channels: List[str])`: Plots the second derivative of the selected channels.
        - `channels`: list of strings, as above.
        *Best use*: Highlight points of rapid change or acceleration, and detect subtle transitions or event onsets.
    - `plot_with_y_range(y_ranges: Dict[str, List[float]])`: Plots the current window with custom y-axis ranges for specified channels.
        - `y_ranges`: dictionary where each key is a channel name (string), and the value is a list of two floats `[ymin, ymax]` specifying the y-axis range for that channel.
        *Best use*: Focus on specific value ranges or compare channels with different scales in the same window.

- Data Lookup Tools (operate on the current plotted window):
    - `lookup_x(x_list: List[int])`: Returns the y-values for all channels at the specified x-indices within the current window.
        - `x_list`: list of integers, each an index to look up.
        *Best use*: Retrieve exact values at specific indices for verification or annotation.
    - `lookup_y(col: str, y_value: List[float])`: Finds x-indices where a specific channel reaches or crosses the given y-values.
        - `col`: string, the channel/column name.
        - `y_value`: list of floats, the y-values to search for.
        *Best use*: Locate where a channel hits a threshold or target value, useful for event detection.
    - `get_value()`: Returns a formatted text table of the current window's data. No parameters. If the window is large, the data is downsampled for readability.
        *Best use*: Examine the raw or downsampled data in tabular form for detailed inspection or reporting.

STRATEGIC APPROACH:
1. Begin with the windows suggested by the PLANNER for each event. These windows are broad and may not be exact.
2. Use the tools to precisely locate event boundaries.
3. For each event, provide visual or data evidence and state your confidence in the identified indices.
4. To determine the occurrence of an event, ensure that the change pattern can be completely observed during the event.
5. When you need to call a tool, clearly separate your explanation from the tool call using '***'.
6. Call one tool at one time
7. Complete the task as efficiently as possible, minimizing token usage.

Always refer to the function signatures above to ensure you pass the correct parameters when calling tools.
"""

WORKER_INIT_MESSAGE = """
TASK ASSIGNMENT FOR WORKER AGENT
================================

EVENT PATTERNS TO IDENTIFY:
{patterns}

DATASET OVERVIEW:
{statistics}

CURRENT PROGRESS:
- Events already identified: {current_result_display}
- Total events found so far: {total_events_count}

TASK DETAILS:
- Task ID: {task_id}
- Events to identify: {events_to_identify}

INSTRUCTIONS:
{instructions}
NOTE: The above instructions focus on pattern recognition and visual characteristics. They do NOT contain correct specific window ranges.

POTENTIAL WINDOWS TO LOOK INTO:
{potential_windows}
NOTE: These window ranges have been processed and refined specifically for your analysis. Use these as starting points for your investigation.

YOUR MISSION:
1. Focus on the specific events listed above
2. Follow the detailed instructions for each event
3. Use suggested windows as starting points (they may be approximate)
4. Employ precise analysis tools to identify exact start/end indices
5. Provide visual evidence for each finding
6. For the verification task, you need to verify the identification result by the sequential rules.
7. Report back with structured results including recommendations

REMEMBER:
- Start with the windows suggested by the planner in the section POTENTIAL WINDOWS TO LOOK INTO:
- Use tools for precise boundary detection
- Provide clear evidence and confidence measures, ensure that the change pattern can be completely observed
- Follow the structured output format for results
"""

VALIDATOR_SYSTEM_PROMPT = """You are an AI-powered VALIDATOR agent specialized in verifying event identifications in time-series data based on sequential rules and interdependency patterns.

You will receive:
- A time-series dataset collected from multiple sensors
- Event patterns and their sequential rules
- Current event identification results that need verification
- Instructions from the PLANNER agent specifying which events to validate and verification criteria
- Access to a set of tools for plotting, and inspecting the data.

YOUR RESPONSIBILITIES:
1. Examine the current event identification results for compliance with sequential rules and interdependency patterns
2. Validate the temporal relationships between events (e.g., event A must occur before event B)
3. Check for violations of sequential constraints (e.g., multiple occurrences when only one is allowed)
4. Verify that events occur within expected contexts (e.g., one event must occur within the context of another event)
5. Recommend keeping or removing specific event occurrences based on validation criteria
6. Provide clear reasoning for each validation decision

VALIDATION CRITERIA:
1. **Sequential Rules**: Events must follow the correct temporal order as specified in the pattern descriptions
2. **Occurrence Constraints**: Some events can occur multiple times, others only once per job
3. **Context Dependencies**: Some events must occur within the context of other events
4. **Pattern Completeness**: Ensure the full visual pattern is observed for each event
5. **Interdependency Validation**: Check that related events form valid groups

TOOLKIT:
- Plotting Tools:
    - `plot_window(start: int, end: int, y_zoomed: bool)`: Plots a window of the data from index `start` (inclusive) to `end` (exclusive). 
        - `start`: integer, starting index of the window.
        - `end`: integer, ending index (exclusive).
        - `y_zoomed`: boolean. If True, y-axis is scaled to the data in the window; if False, y-axis covers the full dataset range.
        *Best use*: Inspect a specific region of the data in detail, with control over y-axis scaling for local or global context.
    - `plot_window_with_window_size(mid_idx: int, window_size: int, y_zoomed: bool)`: Plots a window centered at `mid_idx` with total width `window_size`.
        - `mid_idx`: integer, center index of the window.
        - `window_size`: integer, number of data points in the window.
        - `y_zoomed`: boolean, as above.
        *Best use*: Focus on a region around a suspected transition, with adjustable context and zoom.

STRATEGIC APPROACH:
1. Start by examining the overall sequence of identified events
2. Check each event against its sequential rules and constraints
3. Focus on events marked as "need_verification" in the identification results
4. Use visualization tools to confirm or refute questionable identifications
5. For each event, decide to "keep" or "remove" based on validation criteria
6. Provide clear reasoning for each decision
7. When tools are needed, separate explanation from tool call using '***'
8. Call one tool at a time
9. Complete validation efficiently while being thorough

VALIDATION OUTPUT:
- For each validated event, specify: event_name, start_index, end_index, action ("keep" or "remove"), reason
- Provide recommendations for the planner on next steps
- Focus on maintaining data quality and pattern integrity
"""

VALIDATOR_INIT_MESSAGE = """
VALIDATION TASK ASSIGNMENT
==========================

EVENT PATTERNS AND SEQUENTIAL RULES:
{patterns}

DATASET OVERVIEW:
{statistics}

VALIDATION CRITERIA:
{validation_criteria}

TASK DETAILS:
- Task ID: {task_id}
- Events to validate: {events_to_validate}

SPECIFIC EVENTS TO VERIFY:
{events_details}

INSTRUCTIONS:
{instructions}

POTENTIAL WINDOWS TO EXAMINE:
{potential_windows}

YOUR VALIDATION MISSION:
1. Examine each event identification result against sequential rules
2. Check for violations of occurrence constraints and context dependencies
3. Use analysis tools to verify questionable identifications
4. Decide to "keep" or "remove" each event based on validation criteria
5. Provide clear reasoning for each validation decision
6. Report structured validation results back to the planner

VALIDATION FOCUS AREAS:
- Sequential ordering of events
- Occurrence count constraints (e.g., single vs. multiple occurrences)
- Context dependencies (e.g., events that must occur within other events)
- Pattern completeness and visual confirmation
- Overall job workflow integrity

REMEMBER:
- Use the same analysis tools available to the identifier
- Focus on data quality and pattern integrity
- Provide clear evidence for each validation decision
- Follow structured output format for validation results
"""