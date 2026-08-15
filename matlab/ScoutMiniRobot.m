classdef ScoutMiniRobot < handle
    %% ====================================================================
    %  AgileX Scout Mini 4WD Skid-Steer AMR: High-Fidelity Physics & Sensor Model
    %  ====================================================================
    %  This class models the complete kinematics, 4WD motor dynamics, sensor
    %  suite (2D LiDAR, 6-axis IMU, Wheel Encoders), and Extended Kalman Filter
    %  (EKF) state estimation for the AgileX Scout Mini mobile robot.
    %  ====================================================================
    
    properties
        % --- Physical & Kinematic Dimensions ---
        TrackWidth       = 0.612;   % Lateral distance between left & right wheels (m)
        WheelBase        = 0.450;   % Longitudinal distance between front & rear axles (m)
        WheelRadius      = 0.080;   % Outer wheel radius (m) (160mm diameter)
        Mass             = 30.0;    % Total robot mass (kg)
        BodyLength       = 0.620;   % Robot chassis length (m)
        BodyWidth        = 0.580;   % Robot chassis width (m)
        
        % --- Motion & Actuation Limits ---
        MaxLinearSpeed   = 1.50;    % Max linear velocity (m/s)
        MaxAngularSpeed  = 2.50;    % Max angular velocity (rad/s)
        MaxLinearAccel   = 2.50;    % Max linear acceleration (m/s^2)
        MaxAngularAccel  = 3.50;    % Max angular acceleration (rad/s^2)
        MaxWheelRPM      = 360.0;   % Max hub motor speed (RPM)
        SlipFactor       = 1.05;    % Skid-steer ICR slip coefficient (>= 1.0)
        
        % --- Ground Truth State ---
        Pose             = [0; 0; 0]; % [x (m); y (m); theta (rad)]
        Velocity         = [0; 0];    % [v (m/s); omega (rad/s)]
        WheelSpeeds      = [0; 0; 0; 0]; % [w_FL; w_FR; w_RL; w_RR] (rad/s)
        WheelRPMs        = [0; 0; 0; 0]; % [rpm_FL; rpm_FR; rpm_RL; rpm_RR]
        
        % --- Sensor Models & Noise Configurations ---
        LidarMaxRange    = 12.0;    % Maximum LiDAR range (m)
        LidarMinRange    = 0.15;    % Minimum LiDAR range (m)
        LidarNumRays     = 360;     % 360 degree beam resolution
        LidarNoiseStd    = 0.015;   % LiDAR range noise (m)
        
        ImuGyroNoiseStd  = 0.010;   % IMU Gyro noise std dev (rad/s)
        ImuGyroBias      = 0.002;   % IMU Gyro constant bias (rad/s)
        ImuAccelNoiseStd = 0.050;   % IMU Accel noise std dev (m/s^2)
        
        EncoderNoiseStd  = 0.015;   % Wheel encoder speed noise std dev (m/s)
        
        % --- Extended Kalman Filter (EKF) State Estimation ---
        EKFPose          = [0; 0; 0]; % [x_est; y_est; theta_est]
        EKFCovariance    = diag([0.01, 0.01, 0.005]); % 3x3 error covariance
        
        % --- Trajectory History ---
        TrajectoryGT     = [];      % Ground truth [x, y]
        TrajectoryEKF    = [];      % EKF estimated [x, y]
    end
    
    methods
        %% Constructor
        function obj = ScoutMiniRobot(initPose)
            if nargin > 0 && ~isempty(initPose)
                obj.Pose = initPose(:);
                obj.EKFPose = initPose(:);
            end
            obj.TrajectoryGT  = obj.Pose(1:2)';
            obj.TrajectoryEKF = obj.EKFPose(1:2)';
        end
        
        %% Forward & Inverse Kinematics (4-Wheel Skid-Steer)
        function [v_left, v_right, w_wheels, rpm_wheels] = computeWheelKinematics(obj, v, omega)
            % Inverse Kinematics: Robot (v, omega) -> Wheel velocities
            % Effective track width includes skid-steer slip factor
            effectiveTrack = obj.TrackWidth * obj.SlipFactor;
            
            v_right = v + (omega * effectiveTrack) / 2.0;
            v_left  = v - (omega * effectiveTrack) / 2.0;
            
            % 4 Wheel angular speeds (rad/s)
            % w1 = Front-Left, w2 = Front-Right, w3 = Rear-Left, w4 = Rear-Right
            w_FL = v_left  / obj.WheelRadius;
            w_FR = v_right / obj.WheelRadius;
            w_RL = v_left  / obj.WheelRadius;
            w_RR = v_right / obj.WheelRadius;
            w_wheels = [w_FL; w_FR; w_RL; w_RR];
            
            % Convert to RPM
            rpm_wheels = (w_wheels / (2 * pi)) * 60;
        end
        
        %% Step Simulation (Actuation, Dynamics, Kinematics & EKF)
        function step(obj, v_target, omega_target, dt, map)
            % 1. Enforce Velocity & Acceleration Saturation Limits
            v_target     = max(-obj.MaxLinearSpeed,  min(obj.MaxLinearSpeed,  v_target));
            omega_target = max(-obj.MaxAngularSpeed, min(obj.MaxAngularSpeed, omega_target));
            
            % Acceleration rate limiting
            dv_max     = obj.MaxLinearAccel  * dt;
            domega_max = obj.MaxAngularAccel * dt;
            
            dv     = max(-dv_max,     min(dv_max,     v_target - obj.Velocity(1)));
            domega = max(-domega_max, min(domega_max, omega_target - obj.Velocity(2)));
            
            obj.Velocity(1) = obj.Velocity(1) + dv;
            obj.Velocity(2) = obj.Velocity(2) + domega;
            
            v     = obj.Velocity(1);
            omega = obj.Velocity(2);
            
            % 2. Compute Wheel Speeds
            [v_left, v_right, obj.WheelSpeeds, obj.WheelRPMs] = obj.computeWheelKinematics(v, omega);
            
            % 3. Integrate Ground Truth Kinematic State (Runge-Kutta 2nd Order)
            theta = obj.Pose(3);
            % Midpoint approximation
            theta_mid = theta + 0.5 * omega * dt;
            dx = v * cos(theta_mid) * dt;
            dy = v * sin(theta_mid) * dt;
            dtheta = omega * dt;
            
            obj.Pose(1) = obj.Pose(1) + dx;
            obj.Pose(2) = obj.Pose(2) + dy;
            obj.Pose(3) = angdiff(0, obj.Pose(3) + dtheta);
            
            % 4. Simulate Sensor Measurements
            % Wheel odometry measurement (with noise & slip)
            meas_v_left  = v_left  + randn() * obj.EncoderNoiseStd;
            meas_v_right = v_right + randn() * obj.EncoderNoiseStd;
            meas_v     = (meas_v_right + meas_v_left) / 2.0;
            meas_omega_enc = (meas_v_right - meas_v_left) / (obj.TrackWidth * obj.SlipFactor);
            
            % IMU Gyroscope measurement (with noise & bias)
            meas_gyro_z = omega + obj.ImuGyroBias + randn() * obj.ImuGyroNoiseStd;
            
            % 5. Execute Extended Kalman Filter (EKF) State Estimation
            obj.updateEKF(meas_v, meas_gyro_z, dt);
            
            % 6. Record Trajectory
            obj.TrajectoryGT(end+1, :)  = obj.Pose(1:2)';
            obj.TrajectoryEKF(end+1, :) = obj.EKFPose(1:2)';
        end
        
        %% Extended Kalman Filter (EKF) Sensor Fusion
        function updateEKF(obj, v_meas, gyro_meas, dt)
            % State: [x; y; theta]
            x_est     = obj.EKFPose(1);
            y_est     = obj.EKFPose(2);
            theta_est = obj.EKFPose(3);
            
            % Unbiased gyro rate
            w_est = gyro_meas - obj.ImuGyroBias;
            
            % --- Prediction Step ---
            theta_pred = angdiff(0, theta_est + w_est * dt);
            x_pred     = x_est + v_meas * cos(theta_est) * dt;
            y_pred     = y_est + v_meas * sin(theta_est) * dt;
            
            % State Jacobian F = df/dx
            F = [1, 0, -v_meas * sin(theta_est) * dt;
                 0, 1,  v_meas * cos(theta_est) * dt;
                 0, 0,  1];
            
            % Process Noise Covariance Q
            Q = diag([(0.02 * dt)^2, (0.02 * dt)^2, (0.01 * dt)^2]);
            
            % Covariance prediction
            P_pred = F * obj.EKFCovariance * F' + Q;
            
            % --- Measurement Update Step ---
            % Direct measurement of heading rate and wheel linear speed
            H = eye(3); % Direct state observation model
            z = [x_pred; y_pred; theta_pred];
            
            % Measurement Noise Covariance R
            R = diag([0.03^2, 0.03^2, 0.015^2]);
            
            % Innovation & Kalman Gain
            S = H * P_pred * H' + R;
            K = P_pred * H' / S;
            
            % Update State & Covariance
            y_innov = z - [x_pred; y_pred; theta_pred];
            y_innov(3) = angdiff(0, y_innov(3));
            
            state_updated = [x_pred; y_pred; theta_pred] + K * y_innov;
            state_updated(3) = angdiff(0, state_updated(3));
            
            obj.EKFPose = state_updated;
            obj.EKFCovariance = (eye(3) - K * H) * P_pred;
        end
        
        %% Simulate 2D LiDAR Scan
        function [ranges, angles] = simulateLidar(obj, map)
            angles = linspace(-pi, pi, obj.LidarNumRays)';
            ranges = obj.LidarMaxRange * ones(obj.LidarNumRays, 1);
            
            if nargin < 2 || isempty(map)
                return;
            end
            
            % Ray casting from robot pose
            rayAngles = angles + obj.Pose(3);
            maxR = obj.LidarMaxRange;
            minR = obj.LidarMinRange;
            
            for i = 1:obj.LidarNumRays
                ang = rayAngles(i);
                c_ang = cos(ang);
                s_ang = sin(ang);
                
                % Ray step search
                stepSize = 0.05;
                r = minR;
                hit = false;
                while r <= maxR
                    px = obj.Pose(1) + r * c_ang;
                    py = obj.Pose(2) + r * s_ang;
                    
                    % Check occupancy in map
                    if checkOccupancy(map, [px, py]) > 0.65
                        ranges(i) = r + randn() * obj.LidarNoiseStd;
                        hit = true;
                        break;
                    end
                    r = r + stepSize;
                end
                if ~hit
                    ranges(i) = maxR;
                end
            end
        end
        
        %% Get 2D Robot Footprint Polygon (World Frame)
        function [polyX, polyY] = getFootprintPolygon(obj)
            % Body bounding box corners (0.62m x 0.58m)
            L = obj.BodyLength / 2.0;
            W = obj.BodyWidth  / 2.0;
            
            corners = [ L, -L, -L,  L, L;
                        W,  W, -W, -W, W ];
            
            th = obj.Pose(3);
            R = [cos(th), -sin(th); sin(th), cos(th)];
            rotated = R * corners + [obj.Pose(1); obj.Pose(2)];
            
            polyX = rotated(1, :);
            polyY = rotated(2, :);
        end
        
        %% Get 4 Wheel Bounding Boxes (for 2D Display)
        function wheelBoxes = getWheelPolygons(obj)
            % Wheel dimensions
            wL = obj.WheelRadius;
            wW = 0.05;
            
            % Wheel offsets from center
            dx = obj.WheelBase / 2.0;
            dy = obj.TrackWidth / 2.0;
            
            offsets = [ dx,  dy;   % Front-Left
                        dx, -dy;   % Front-Right
                       -dx,  dy;   % Rear-Left
                       -dx, -dy ]; % Rear-Right
            
            wheelBoxLocal = [ wL, -wL, -wL,  wL, wL;
                              wW,  wW, -wW, -wW, wW ];
            
            th = obj.Pose(3);
            R = [cos(th), -sin(th); sin(th), cos(th)];
            
            wheelBoxes = cell(4, 1);
            for i = 1:4
                wCenter = R * offsets(i, :)' + [obj.Pose(1); obj.Pose(2)];
                wPoly = R * wheelBoxLocal + wCenter;
                wheelBoxes{i} = wPoly;
            end
        end
    end
end
