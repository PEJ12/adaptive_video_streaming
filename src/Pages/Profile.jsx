import React, { useState, useContext, useEffect, useRef } from "react";
import { getAuth, updateProfile, signOut } from "firebase/auth";
import { db } from "../Firebase/FirebaseConfig";
import {
  ref,
  uploadBytesResumable,
  getDownloadURL,
  getStorage,
} from "firebase/storage";
import { useNavigate } from "react-router-dom";
import { Fade } from "react-reveal";
import toast, { Toaster } from "react-hot-toast";

import { AuthContext } from "../Context/UserContext";
import WelcomePageBanner from "../images/WelcomePageBanner.jpg";

import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";

function Profile() {
  //User는 Firebase에서 로그인한 사용자 정보를 담고 있다.
  const { User } = useContext(AuthContext);

  const [profilePic, setProfilePic] = useState("");
  const [newProfielPicURL, setNewProfielPicURL] = useState("");
  const [newProfielPic, setNewProfielPic] = useState("");
  const [isUserNameChanged, setIsUserNameChanged] = useState(false);
  const [userName, setUserName] = useState("");
  const [isMyListUpdated, setisMyListUpdated] = useState(false);

  const navigate = useNavigate();

  //로그인 된 사용자의 프로필 사진을 상태에 저장하는 초기 실행 코드
  useEffect(() => {
    if (User != null) { //User : 현재 로그인 된 사용자 정보
      console.log(User.photoURL, "hello");
      setProfilePic(User.photoURL); 
    }
  }, []);

  const inputRef = useRef(null);

  const handleClick = () => {
    inputRef.current.click();
  };

  function notify() {
    toast.success("  Data Updated Sucessfuly  ");
  }

  //사용자가 프로필 사진 직접 선택했을 때 파일 객체와 미리보기 url을 상태에 저장하는 함수
  //실행 시점 : 사진 선택 즉시 (즉, 상태 저장, 이미지 미리보기)
  const handleFileChange = (event) => {
    const fileObj = event.target.files[0]; //사용자가 선택한 파일 객체
    setNewProfielPic(fileObj); //파일 객체를 newProfilePic 상태에 저장
    // 새로 선택한 이미지의 URL을 생성하여 상태에 저장 (브라우저 미리보기 위해)
    //URL.createObjectURL(file)은 해당 파일을 웹 주소처럼 표시할 수 있게 해준다.
    setNewProfielPicURL(URL.createObjectURL(fileObj)); 
    if (!fileObj) { //사용자가 아무 파일도 선택하지 않았을때
      return; //함수 종료
    }
    console.log("fileObj is", fileObj); // 선택한 파일 정보 콘솔에 출력
    //동일한 파일을 다시 업로드하려고 할 때도 onChange 이벤트가 발생하게 하려는 처리
    event.target.value = null; //파일 선택 후 input 초기화
  };


  //사용자가 프로필 이름을 변경하려고 할 때, 해당 이름을 firebase auth에 업데이트하는 함수
  const changeUserName = (e) => {
    e.preventDefault(); 
    if (isUserNameChanged) { //사용자가 입력창에 뭔가를 입력했는지 확인  
      if (userName !== "") { //사용자 이름 업데이트
        const auth = getAuth();
        //현재 로그인 된 사용자를 가져와서 새 이름으로 업데이트.
        updateProfile(auth.currentUser, { displayName: userName })
          .then(() => {
            notify(); //성공 메세지
          })
          .catch((error) => {
            alert(error.message); //에러 메세지
          });
      } else { //변경된 이름이 없으면 상태 초기화
        setIsUserNameChanged(false);
      }
    }

    // 선택한 사진 업로드 후 프로필 사진 업데이트
    if (newProfielPic != "") { //사용자가 새로 프로필 이미지 선택하면
      const storage = getStorage();
      const storageRef = ref(storage, `/ProfilePics/${User.uid}`);
      // Firebase Storage에 새 프로필 사진 업로드
      const uploadTask = uploadBytesResumable(storageRef, newProfielPic);

      uploadTask.on( //업로드 상태 모니터링
        "state_changed", 
        (snapshot) => { //진행률 계산
          const prog = Math.round(
            (snapshot.bytesTransferred / snapshot.totalBytes) * 100
          );
        },
        (error) => { //에러 메세지
          alert(error.message);
          alert(error.code);
        },
        () => { //파일 업로드 완료 후 실제 접근 URL 가져오기
          // 이름 변경 함수 안에 사진 변경도 같이 있는 이유 : 
          // save and continue 버튼을 클릭했을 때, 이름과 사진을 동시에 저장

          // 이 때 url은 사용자가 직접 고른 파일을 Firebase Storage에
          // 업로드한 후, 그 업로드된 이미지의 다운로드 URL
          getDownloadURL(uploadTask.snapshot.ref).then((url) => {
            console.log(url, "This is the new Url for Profile Pic");
            setProfilePic(url);
            const auth = getAuth();
            //Firebase Authentication의 사용자 정보 중 photoURL 값을 새로 받은 이미지 주소로 업데이트
            updateProfile(auth.currentUser, { photoURL: url })
              .then(() => { 
                notify(); //성공메세지
                setisMyListUpdated(true);
              })
              .catch((error) => { //에러 메세지
                alert(error.message);
              });
          });
        }
      );
    }
  };
  //기본 아바타 4개 사진은 이 함수만 실행.
  // 업로드 파일의 url이나 기본 4개 사진의 url 받아와서 프로필에 반영   
  //이미지url을 firebase auth에 업데이트하는 함수
  //save and continue 버튼을 클릭했을 때 호출된다. (프로필이 4개에서 5개로 추가되는 게 아니고 자기 프로필 사진만 바뀜)
  const updateProfilePic = (imageURL) => {
    const auth = getAuth();
    //auth.currentUser는 현재 로그인된 사용자 정보를 나타낸다.
    // User 중 photoURL 값을 새로 지정된 이미지 주소로 업데이트
    updateProfile(auth.currentUser, { photoURL: imageURL })
      .then(() => { //성공시 상태 업데이트
        setProfilePic(User.photoURL);
        notify(); //성공 메세지
      })
      .catch((error) => {
        alert(error.message); //에러 메세지
      });
  };

  //로그아웃
  const SignOut = () => {
    const auth = getAuth();
    signOut(auth)
      .then(() => {
        navigate("/"); //성공시 홈화면 이동
      })
      .catch((error) => { //실패시 에러 메세지
        alert(error.message);
      });
  };

  return (
    <div>
      <div
        className="flex h-screen justify-center items-center"
        style={{
          backgroundImage: `linear-gradient(0deg, hsl(0deg 0% 0% / 73%) 0%, hsl(0deg 0% 0% / 73%) 35%), url(${WelcomePageBanner})`,
        }}
      >
        {isMyListUpdated ? (
          <Toaster
            toastOptions={{
              style: {
                padding: "1.5rem",
                backgroundColor: "##f4fff4",
                borderLeft: "6px solid green",
              },
            }}
          />
        ) : null}
        <Fade>
          <div className="bg-[#000000bf] p-5 md:p-12 rounded-md">
            <h1 className="text-4xl text-white font-bold mb-4 md:mb-8">
              Edit your Profile
            </h1>
            <div className="flex justify-center flex-col items-center md:flex-row md:items-start">
              <img
                className={
                  profilePic
                    ? "h-28 w-28 rounded-full cursor-pointer mb-3 md:mr-16"
                    : "h-28 w-28 rounded-full cursor-pointer mb-3 md:mr-16"
                }
                src={
                  profilePic
                    ? `${profilePic}`
                    : `https://www.citypng.com/public/uploads/preview/profile-user-round-blue-icon-symbol-download-png-11639594337tco5j3n0ix.png`
                }
                alt="NETFLIX"
              />
              <div>
                <hr className="mb-2 h-px bg-gray-500 border-0 dark:bg-gray-700"></hr>
                <h1 className="text-white text-lg font-medium mb-2">
                  User Name
                </h1>
                <input
                  type="text"
                  onChange={(e) =>
                    setUserName(e.target.value) || setIsUserNameChanged(true)
                  }
                  className="block w-full rounded-md bg-stone-900 text-white border-gray-300 p-2 mb-6 focus:border-indigo-500 focus:ring-indigo-500 sm:text-base"
                  placeholder={User ? User.displayName : null}
                />
                <h1 className="text-white text-lg font-medium mb-2">Email</h1>
                <h1 className="text-white text-xl bg-stone-900 p-2 rounded mb-4 md:pr-52">
                  {User ? User.email : null}
                </h1>
                <h1 className="text-white text-xl p-2 rounded mb-4">
                  Unique ID : {User ? User.uid : null}
                </h1>
                <hr className="h-px bg-gray-500 border-0 mb-4 md:mb-10 dark:bg-gray-700"></hr>

                <h1 className="text-white text-lg font-medium mb-4">
                  Who is Watching ?
                </h1>
                <div className="flex justify-between cursor-pointer mb-4 md:mb-8">
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://i.pinimg.com/originals/ba/2e/44/ba2e4464e0d7b1882cc300feceac683c.png"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://i.pinimg.com/originals/ba/2e/44/ba2e4464e0d7b1882cc300feceac683c.png"
                  />
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://i.pinimg.com/736x/db/70/dc/db70dc468af8c93749d1f587d74dcb08.jpg"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://i.pinimg.com/736x/db/70/dc/db70dc468af8c93749d1f587d74dcb08.jpg"
                  />
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"
                  />
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://ih0.redbubble.net/image.618363037.0853/flat,1000x1000,075,f.u2.jpg"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://ih0.redbubble.net/image.618363037.0853/flat,1000x1000,075,f.u2.jpg"
                  />
                  <input
                    style={{ display: "none" }}
                    ref={inputRef}
                    type="file"
                    onChange={handleFileChange}
                  />
                  <svg
                    onClick={handleClick}
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-12 w-12 text-stone-600 cursor-pointer"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                {newProfielPicURL ? (
                  <img className="h-30 w-72" src={newProfielPicURL} />
                ) : null}
              </div>
            </div>
            <div className="flex justify-between mt-4">
              <button
                onClick={SignOut}
                className="flex items-center border-[0.7px] border-white text-white font-medium sm:font-bold text-xs px-14 md:px-24 md:text-xl  py-3 rounded shadow hover:shadow-lg hover:bg-white hover:border-white hover:text-blue-700 outline-none focus:outline-none mr-3 mb-1 ease-linear transition-all duration-150"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6 mr-2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M22 10.5h-6m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z"
                  />
                </svg>
                SignOut
              </button>
              {userName != "" || newProfielPic != "" ? (
                <button
                  onClick={changeUserName}
                  className="flex items-center bg-blue-700 text-white font-medium sm:font-bold text-xs px-10 md:px-16 md:text-xl  py-3 rounded shadow hover:shadow-lg hover:bg-white hover:text-blue-700 outline-none focus:outline-none mr-3 mb-1 ease-linear transition-all duration-150"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-6 h-6 mr-2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
                    />
                  </svg>
                  Save and continue
                </button>
              ) : (
                <button
                  onClick={() => navigate("/")}
                  className="flex items-center bg-blue-700 text-white font-medium sm:font-bold text-xs px-10 md:px-16 md:text-xl  py-3 rounded shadow hover:shadow-lg hover:bg-white hover:text-blue-700 outline-none focus:outline-none mr-3 mb-1 ease-linear transition-all duration-150"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-6 h-6 mr-2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
                    />
                  </svg>
                  Back to Home
                </button>
              )}
            </div>
          </div>
        </Fade>
      </div>
    </div>
  );
}

export default Profile;
