import numpy as np
import torch



class DeviceMethods:
    
    @staticmethod
    def crash_index(acc_norm,configs):
        crash_energy = configs["crash_energy"]

        for i,val in enumerate(acc_norm):
            if val > crash_energy:
                break
        return i
    
    @staticmethod
    def find_a0(acc,configs):
        """
        find a window where the car is standing still (in a rest <=> only normal force is active)
        """
        # read configs:
        a0_win_size = configs["a0_win_size"]
        norm_tolerance = configs["acc_noise_tolerance_on_norm"]
        noise_tolerance = configs["acc_noise_tolerance"]
        
        a0 = None
        acc_norm = np.linalg.norm(acc, axis=1)
        # choose signal before crash
        crash_ind = DeviceMethods.crash_index(acc_norm,configs)
        acc = acc.iloc[:,:crash_ind]
        acc_norm = acc_norm[:crash_ind]
        
        for i in range(len(acc_norm) - a0_win_size): 
            # norm
            curr_wind = acc_norm[i:i+a0_win_size]
            if not (abs(curr_wind - 1) <= norm_tolerance).all(): 
                continue
            # absolute value
            curr_wind = acc.iloc[i:i+a0_win_size].to_numpy()
            max_vals = np.max(curr_wind,axis=0)
            min_vals = np.min(curr_wind,axis=0)
            if not (abs(max_vals - min_vals) <= noise_tolerance).all(): 
                continue
            a0 = np.mean(curr_wind, axis=0).tolist()
            noise_tolerance = max(abs(max_vals - min_vals))

        return a0

    @staticmethod
    def is_bp(button_signal):
        """
        returns dict {"Decision": True/False, "Reason": "..."}
        """
        if isinstance(button_signal,list):
            if all(button_signal):
                return {"Decision": True, "Reason": "All samples are on"}

            if any(button_signal):
                return {"Decision": False, "Reason": "Not all samples are on"}
            
            return {"Decision": False, "Reason": "All samples are off"}
            
        if button_signal:
            return {"Decision": True, "Reason": "Sample is on"}
        else:
            return {"Decision": False, "Reason": "Sample is off"}


    @staticmethod
    def orientation_estimation(a0, configs):
        
        atol = configs["orientation_atol"]
        ws_bias_g = configs["orientation_ws_bias_g"]
        
        if (np.isclose(a0[0], ws_bias_g, atol=atol) and np.isclose(a0[1], 0, atol=atol)): 
            if a0[0] > a0[1]:
                return "aligned"

        if (np.isclose(a0[0], -1*ws_bias_g, atol=atol) and np.isclose(a0[1], 0, atol=atol)):
            if a0[0] < a0[1]:
                return "upsidown"
        
        if (np.isclose(a0[0], 0, atol=atol) and np.isclose(a0[1], ws_bias_g, atol=atol)): 
            if a0[0] < a0[1]:
                return "left"
        
        if (np.isclose(a0[0], 0, atol=atol) and np.isclose(a0[1], -1*ws_bias_g, atol=atol)):
            if a0[0] > a0[1]:
                return "right"
        
        return "aligned"
    
    @staticmethod
    def find_init_cond(orient, ws_angle):
            orintation_dict = {"left": 90, "right": 270,"upsidown": 0,"aligned": 180}
            return [0, ws_angle,orintation_dict[orient]] 

    @staticmethod
    def torch_search(a0, init_cond, configs): 
        
        def function(e):
            return torch.stack((
                    torch.cos(e[1])*torch.sin(e[0])*torch.sin(e[2])-torch.cos(e[2])*torch.sin(e[1]) ,  
                    torch.cos(e[1])*torch.cos(e[2])*torch.sin(e[0])+torch.sin(e[1])*torch.sin(e[2]) ,  
                    torch.cos(e[0])*torch.cos(e[1])
                    ))   
        
        # read configs
        lr = configs["lr"]
        momentum =  configs["momentum"]
        base_lr = configs["base_lr"]
        max_lr = configs["max_lr"]
        num_iter = configs["num_iter"]
        
        naive_guess_rad = [np.deg2rad(x) for x in init_cond]            
        guess = torch.tensor(naive_guess_rad, dtype=torch.float32)
        guess.requires_grad=True
        target = torch.tensor(a0, dtype=torch.float32) 
        opt = torch.optim.SGD([guess], lr=lr, momentum=momentum)
        scheduler = torch.optim.lr_scheduler.CyclicLR(opt, base_lr=base_lr, max_lr=max_lr)
        num_iter = num_iter
        losses = []
        guesses = []
        for i in range(num_iter):
            y_pred = function(guess)
            loss = torch.sum(torch.abs((y_pred-target)+1e-15))
            opt.zero_grad()
            loss.backward()
            losses.append(loss.data)
            guesses.append(guess.clone())
            opt.step()
            scheduler.step()

        min_ind = np.argmin(losses)
        best_guess = guesses[min_ind].detach().numpy() # best guess
        return [float(np.rad2deg(x)) for x in best_guess]

